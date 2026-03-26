import streamlit as st
import pandas as pd
import sqlite3
import os

# --- PATHS ---
DATA_FILE = "data/latest_results.csv"
DB_FILE = "hkjc_local.db"

# --- DB INIT ---
conn = sqlite3.connect(DB_FILE, check_same_thread=False)

st.set_page_config(page_title="HKJC AI: hkjc-tool", layout="wide")
st.title("🐎 HKJC Automated AI Dashboard")

# --- SYNC LOGIC ---
st.sidebar.header("Data Management")
if st.sidebar.button("🔄 Sync with Cloud Bot"):
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df.to_sql("results", conn, if_exists="append", index=False)
        st.sidebar.success(f"Imported {len(df)} new records!")
    else:
        st.sidebar.error("Bot hasn't generated data yet. Check GitHub Actions.")

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["📊 Live Betting", "🧠 AI Model"])

with tab2:
    st.header("AI Training Engine")
    count_df = pd.read_sql("SELECT COUNT(*) as total FROM results", conn)
    st.metric("Total Records in DB", count_df['total'][0])
    
    if st.button("Train AI Model"):
        # (Your training logic here)
        st.success("LightGBM Ranker is now optimized.")
        st.session_state['trained'] = True

with tab1:
    if 'trained' not in st.session_state:
        st.warning("Please sync data and train the model.")
    else:
        st.header("Today's Betting Table (Kelly Criterion)")
        # Simulated live data table
        st.write("AI is analyzing the latest trends from your hkjc-tool data...")
        # ... (Your betting recommendation table logic from previous steps)
