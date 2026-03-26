import streamlit as st
import pandas as pd
import numpy as np
from lightgbm import LGBMRanker

# --- APP STYLING ---
st.set_page_config(page_title="HKJC Quant", layout="centered")
st.title("🐎 HKJC AI Terminal")

# --- SIDEBAR (iPad Touch Friendly) ---
st.sidebar.header("Bankroll Management")
balance = st.sidebar.number_input("Current Balance ($)", value=10000)
risk = st.sidebar.slider("Risk (Kelly %)", 0.1, 1.0, 0.25)

# --- TABS FOR MOBILE NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📊 Live Bets", "📈 Analysis", "⚙️ Sync"])

with tab3:
    st.subheader("Database Sync")
    if st.button("Update Historical Data"):
        st.write("Scraping HKJC... Done.")

with tab1:
    st.subheader("Top Value Recommendations")
    # This data would come from your Scraper/ML model
    data = {
        "Horse": ["Golden Sixty", "Romantic Warrior", "Lucky Sweynesse"],
        "Odds": [2.4, 4.1, 8.5],
        "AI_Prob": [0.55, 0.30, 0.15]
    }
    df = pd.DataFrame(data)
    
    # Kelly Logic
    df['EV'] = (df['AI_Prob'] * df['Odds']) - 1
    df['Rec_Bet'] = ((df['Odds'] - 1) * df['AI_Prob'] - (1 - df['AI_Prob'])) / (df['Odds'] - 1)
    df['Bet_Amount'] = (df['Rec_Bet'] * balance * risk).clip(lower=0).round(0)

    # Display as a clean mobile list
    for index, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**{row['Horse']}** (Odds: {row['Odds']})")
                st.caption(f"AI Win Prob: {row['AI_Prob']*100:.0f}% | Edge: {row['EV']*100:.1f}%")
            with col2:
                if row['EV'] > 0.15:
                    st.success(f"BET: ${row['Bet_Amount']}")
                else:
                    st.info("No Value")
            st.divider()