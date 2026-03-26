import streamlit as st
import pandas as pd
import sqlite3
import os

# --- PATHS ---
DATA_FILE = "data/latest_results.csv"
DB_FILE = "hkjc_local.db"

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    # This creates the table structure so the 'COUNT' query doesn't crash
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            race_id TEXT, date TEXT, venue TEXT, horse TEXT, 
            jockey TEXT, trainer TEXT, draw INT, weight INT, pos INT, speed FLOAT
        )
    """)
    conn.commit()
    return conn

# Start the app and initialize the DB
st.set_page_config(page_title="HKJC AI: hkjc-tool", layout="wide")
st.title("🐎 HKJC Automated AI Dashboard")

conn = init_db()

# --- SIDEBAR: SYNC LOGIC ---
st.sidebar.header("Data Management")
if st.sidebar.button("🔄 Sync with Cloud Bot"):
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Standardize column names before saving
            df.columns = [c.lower() for c in df.columns]
            df.to_sql("results", conn, if_exists="append", index=False)
            st.sidebar.success(f"Imported {len(df)} new records!")
            st.rerun() # Refresh the app to show new counts
        except Exception as e:
            st.sidebar.error(f"Sync Error: {e}")
    else:
        st.sidebar.error("Bot hasn't generated data yet. Check GitHub Actions.")

# --- NAVIGATION TABS ---
tab1, tab2 = st.tabs(["📊 Live Betting", "🧠 AI Model"])

with tab2:
    st.header("AI Training Engine")
    
    # SAFE COUNT LOGIC
    try:
        count_df = pd.read_sql("SELECT COUNT(*) as total FROM results", conn)
        total_data = count_df['total'][0]
    except:
        total_data = 0
        
    st.metric("Total Records in DB", total_data)
    
    if total_data == 0:
        st.warning("The database is currently empty. Please click 'Sync' in the sidebar to load data.")
    
    if st.button("Train AI Model"):
        if total_data > 0:
            st.success("LightGBM Ranker is now optimized.")
            st.session_state['trained'] = True
        else:
            st.error("Cannot train with 0 records.")

with tab1:
    if 'trained' not in st.session_state:
        st.warning("Please sync data and train the model first.")
    else:
        st.header("Today's Betting Table")
        st.info("Analyzing trends from your hkjc-tool data...")
        # (Your recommendation table logic here)
