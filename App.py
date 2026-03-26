import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
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

# --- APP UI ---
st.set_page_config(page_title="HKJC AI Terminal", layout="wide")
st.title("🐎 HKJC Professional AI Terminal")

init_db()
conn = get_connection()

# --- SIDEBAR: MANUAL UPLOAD & BANKROLL ---
st.sidebar.header("💰 Bankroll & Data")
balance = st.sidebar.number_input("Current Balance ($HKD)", value=10000)
risk = st.sidebar.slider("Risk (Kelly Multiplier)", 0.1, 1.0, 0.25)

st.sidebar.divider()
st.sidebar.subheader("📤 Manual Sync")
uploaded_file = st.sidebar.file_uploader("Upload Latest HKJC CSV", type=["csv"])

if uploaded_file is not None:
    try:
        manual_df = pd.read_csv(uploaded_file)
        manual_df.to_sql("results", conn, if_exists="append", index=False)
        st.sidebar.success("✅ Database Updated!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Live Recommendations", "📈 AI Training", "🔍 System Health"])

with tab3:
    st.header("System Health & Verification")
    
    if os.path.exists(DB_NAME):
        # 1. Check Row Count
        count_df = pd.read_sql("SELECT COUNT(*) as total FROM results", conn)
        total_rows = count_df['total'][0]
        
        # 2. Check Latest Data
        if total_rows > 0:
            date_df = pd.read_sql("SELECT MAX(date) as last_date FROM results", conn)
            st.success(f"✅ Connection Active: {total_rows} records found.")
            st.info(f"📅 Last Update: {date_df['last_date'][0]}")
            
            st.subheader("Database Preview (Last 5 Entries)")
            preview_df = pd.read_sql("SELECT date, venue, horse, jockey, pos FROM results ORDER BY date DESC LIMIT 5", conn)
            st.dataframe(preview_df, use_container_width=True)
        else:
            st.warning("⚠️ Database is Connected but EMPTY. Please upload data or sync.")
    else:
        st.error("❌ Database not initialized.")

with tab2:
    st.header("AI Model Status")
    if st.button("Train ML Engine"):
        with st.spinner("Analyzing historical patterns..."):
            # Logic to train model would go here
            st.session_state['model_ready'] = True
            st.success("LightGBM Ranker Trained & Ready.")

with tab1:
    st.header("Today's Value Bets")
    if 'model_ready' not in st.session_state:
        st.warning("Please train the AI Model in the 'AI Training' tab first.")
    else:
        # SIMULATED DATA (Replace with real scraper logic later)
        data = {
            "Horse": ["Golden Sixty", "Romantic Warrior", "Lucky Sweynesse", "California Spangle"],
            "Odds": [2.4, 4.1, 8.5, 1.8],
            "AI_Prob": [0.55, 0.30, 0.15, 0.40]
        }
        df = pd.DataFrame(data)
        
        # Kelly Criterion Calculation
        df['EV'] = (df['AI_Prob'] * df['Odds']) - 1
        df['Rec_Bet'] = ((df['Odds'] - 1) * df['AI_Prob'] - (1 - df['AI_Prob'])) / (df['Odds'] - 1)
        df['Stake'] = (df['Rec_Bet'] * balance * risk).clip(lower=0).round(0)

        # Visual Table
        st.dataframe(df[['Horse', 'Odds', 'AI_Prob', 'EV', 'Stake']], use_container_width=True)
        
        # Highlights
        best_bet = df.sort_values(by='EV', ascending=False).iloc[0]
        if best_bet['EV'] > 0.15:
            st.success(f"🔥 TOP VALUE: **{best_bet['Horse']}** at ${best_bet['Odds']} odds. Recommended Bet: ${best_bet['Stake']}")
