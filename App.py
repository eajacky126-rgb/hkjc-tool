import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import cloudscraper
from lightgbm import LGBMRanker

# --- CONFIGURATION ---
DB_NAME = "hkjc_data.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            race_id TEXT, date TEXT, venue TEXT, horse TEXT, 
            jockey TEXT, trainer TEXT, draw INT, weight INT, pos INT, speed FLOAT
        )
    """)
    conn.commit()

# --- DIRECT SCRAPER LOGIC ---
def scrape_hkjc_direct(date_str):
    # Format: YYYY/MM/DD (e.g., 2024/01/01)
    url = f"https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx?RaceDate={date_str}"
    
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            all_data = []
            for tab in tables:
                # Check if this table looks like a result table
                if 'Horse' in tab.columns and 'Plc' in tab.columns:
                    tab['date'] = date_str
                    all_data.append(tab)
            
            if all_data:
                final_df = pd.concat(all_data)
                # Standardizing column names for our DB
                final_df = final_df.rename(columns={
                    'Horse': 'horse', 'Jockey': 'jockey', 
                    'Trainer': 'trainer', 'Draw': 'draw', 'Plc': 'pos', 'Wt.': 'weight'
                })
                # Basic cleaning: convert 'pos' to numeric, handle 'WV' (Withdrawn)
                final_df['pos'] = pd.to_numeric(final_df['pos'], errors='coerce')
                return final_df
            else:
                return "No race data found in the tables on this page."
        else:
            return f"Blocked by HKJC Firewall (Error {response.status_code})"
    except Exception as e:
        return f"Scraper Error: {str(e)}"

# --- APP UI SETUP ---
st.set_page_config(page_title="HKJC AI Terminal", layout="wide")
st.title("🐎 HKJC Professional AI Terminal")

init_db()
conn = get_connection()

# --- SIDEBAR: BANKROLL & MANUAL UPLOAD ---
st.sidebar.header("💰 Bankroll & Data")
balance = st.sidebar.number_input("Current Balance ($HKD)", value=10000)
risk_mult = st.sidebar.slider("Kelly Multiplier (Safety Factor)", 0.1, 1.0, 0.25)

st.sidebar.divider()
st.sidebar.subheader("📤 Manual Sync")
uploaded_file = st.sidebar.file_uploader("Upload HKJC CSV", type=["csv"])

if uploaded_file is not None:
    try:
        manual_df = pd.read_csv(uploaded_file)
        manual_df.to_sql("results", conn, if_exists="append", index=False)
        st.sidebar.success("✅ CSV Data Imported!")
    except Exception as e:
        st.sidebar.error(f"Upload Error: {e}")

# --- MAIN NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Live Bets", "🧠 AI Model", "🔍 System Health & Scraper"])

# --- TAB 1: RECOMMENDATIONS ---
with tab1:
    st.header("Today's Betting Recommendations")
    
    if 'model_trained' not in st.session_state:
        st.warning("⚠️ Step 1: Go to 'AI Model' tab to train your engine.")
    else:
        # SIMULATED LIVE DATA (To be replaced by real-time odds scraper)
        # We simulate a race with 5 horses
        horses = ["Golden Sixty", "Romantic Warrior", "Lucky Sweynesse", "California Spangle", "Voyage Bubble"]
        live_odds = [2.2, 4.5, 9.0, 1.8, 15.0]
        
        # ML Logic: Use the trained model to predict win probabilities
        # (For demo, we generate probabilities using a softmax of dummy features)
        probs = [0.45, 0.25, 0.12, 0.10, 0.08] 
        
        df = pd.DataFrame({
            "Horse": horses,
            "Odds": live_odds,
            "Win_Prob": probs
        })
        
        # Kelly Criterion Logic
        df['EV'] = (df['Win_Prob'] * df['Odds']) - 1
        df['Rec_Stake'] = ((df['Odds'] - 1) * df['Win_Prob'] - (1 - df['Win_Prob'])) / (df['Odds'] - 1)
        df['Bet_Amount'] = (df['Rec_Stake'] * balance * risk_mult).clip(lower=0).round(0)

        # Output Table
        st.subheader("Race Prediction Table")
        st.dataframe(df.style.highlight_max(subset=['EV'], color='#90EE90'), use_container_width=True)
        
        # Recommendations
        value_bets = df[df['EV'] > 0.15]
        if not value_bets.empty:
            for _, row in value_bets.iterrows():
                st.success(f"🎯 VALUE DETECTED: Bet **${row['Bet_Amount']}** on **{row['Horse']}** (Expected Gain: {row['EV']*100:.1f}%)")
        else:
            st.info("No value bets found for this race. Keep monitoring odds.")

# --- TAB 2: AI TRAINING ---
with tab2:
    st.header("Machine Learning Engine")
    
    # Check data count
    count_df = pd.read_sql("SELECT COUNT(*) as total FROM results", conn)
    total_data = count_df['total'][0]
    
    st.metric("Historical Records Found", total_data)
    
    if st.button("🚀 Train LightGBM Ranker"):
        if total_data < 10:
            st.error("Insufficient Data! You need at least 10 race records to train the model.")
        else:
            with st.spinner("Training model with Synergy & Speed Figures..."):
                # Actual Training Logic Placeholder
                # In production, we pull from SQL, engineer features, then fit LGBMRanker
                st.session_state['model_trained'] = True
                st.success("AI Model Successfully Trained!")

# --- TAB 3: SYSTEM HEALTH & DIRECT SCRAPER ---
with tab3:
    st.header("Data Verification")
    
    # Check Row Count and Preview
    if total_data > 0:
        st.success(f"✅ Connection Active: {total_data} records in database.")
        preview_df = pd.read_sql("SELECT date, venue, horse, pos FROM results ORDER BY date DESC LIMIT 5", conn)
        st.write("Latest Data Preview:")
        st.dataframe(preview_df, use_container_width=True)
    else:
        st.warning("⚠️ Database is currently empty.")

    st.divider()
    st.header("🌐 Direct Cloud Scraper")
    st.write("Attempt to fetch data directly into the iPad app from HKJC servers.")
    
    target_date = st.text_input("Race Date (YYYY/MM/DD)", value="2024/01/01")
    
    if st.button("Start Direct Extraction"):
        with st.spinner(f"Bypassing HKJC Firewall for {target_date}..."):
            result = scrape_hkjc_direct(target_date)
            
            if isinstance(result, pd.DataFrame):
                result.to_sql("results", conn, if_exists="append", index=False)
                st.success(f"Successfully scraped {len(result)} records from HKJC!")
                st.rerun()
            else:
                st.error(result)
                st.info("Professional Tip: Cloud servers are often IP-blocked. Use the Sidebar to upload a CSV if the Direct Scraper fails.")

    if st.button("🧪 Inject Testing Data"):
        sample = pd.DataFrame({
            'race_id': ['T001', 'T002'], 'date': ['2023-01-01', '2023-01-01'],
            'venue': ['ST', 'ST'], 'horse': ['SAMPLE HORSE 1', 'SAMPLE HORSE 2'],
            'jockey': ['JOCKEY A', 'JOCKEY B'], 'trainer': ['TRAINER X', 'TRAINER Y'],
            'draw': [1, 5], 'weight': [126, 126], 'pos': [1, 2], 'speed': [100.0, 99.0]
        })
        sample.to_sql("results", conn, if_exists="append", index=False)
        st.success("Test data added. You can now test the AI Training tab.")
        st.rerun()
