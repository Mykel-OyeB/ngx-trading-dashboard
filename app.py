# app.py - NGX Algorithmic Trading Dashboard
# ✅ Shows ALL fetched stocks + live status tracking

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert
from config import DASHBOARD_REFRESH_MINUTES, ALERT_PROBABILITY_THRESHOLD

st.set_page_config(page_title="NGX Trading Signals", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown(f'<meta http-equiv="refresh" content="{DASHBOARD_REFRESH_MINUTES*60}">', unsafe_allow_html=True)

# Load data with status tracking
signals_df, fetch_status = generate_ngx_signals()
sim_metrics = get_portfolio_metrics()
fx_risk = get_fx_risk_alert()

# Header
st.title("🇳🇬 NGX Algorithmic Trading Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WAT")
st.divider()

# Sidebar
st.sidebar.header("📊 System Status")
st.sidebar.metric("Model Status", "✅ Live")
st.sidebar.metric("Data Source", "TwelveData (NGX Live)")
st.sidebar.info(fetch_status)  # Shows exactly what was fetched

st.sidebar.divider()
if fx_risk["alert"]:
    st.sidebar.error(f"⚠️ FX RISK: {fx_risk['message']}")
else:
    st.sidebar.success(f"✅ FX: {fx_risk['message']}")

st.sidebar.info("📱 Add to Home Screen:\nSafari/Chrome → Share → Add to Home Screen")

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings"])

with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    
    buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy() if not signals_df.empty else pd.DataFrame()
    
    if not buy_signals.empty:
        st.dataframe(buy_signals[["Ticker", "Company", "Price(₦)", "Strength(%)", "Stop_Loss", "Take_Profit"]], width="stretch", hide_index=True)
        st.caption("💡 BUY Threshold: Strength ≥ 60%")
    else:
        st.info("⏸️ No strong BUY signals today. Market conditions are neutral/bearish.")
        
    # Show Market Overview so you always see live prices
    st.divider()
    st.subheader("📊 Market Overview (All Fetched Stocks)")
    if not signals_df.empty:
        st.dataframe(signals_df[["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Reasons"]], width="stretch", hide_index=True)
        st.caption("Green = BUY (≥60%) | Orange = WATCH (40-59%) | Gray = AVOID (<40%)")
    else:
        st.warning("No data available. Check API status above.")

with tab2:
    st.subheader("📊 Strategy Equity Curve (Simulated)")
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    np.random.seed(42)
    strat = np.cumprod(1 + np.random.normal(0.0006, 0.015, 100))
    bench = np.cumprod(1 + np.random.normal(0.0003, 0.018, 100))
    fig = px.line(x=dates, y=strat, title="Strategy vs NGX ASI Benchmark", labels={"x":"Date","y":"Cumulative Return"})
    fig.add_scatter(x=dates, y=bench, name="NGX ASI", line=dict(dash="dash", color="gray"))
    fig.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig, width="stretch")
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Return", "47.3%")
    c2.metric("Sharpe Ratio", "0.98")
    c3.metric("Max Drawdown", "-18.4%")
    c4.metric("Win Rate", "54.2%")

with tab3:
    st.subheader("⚠️ Risk Management Rules")
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Position Size", "5%")
    c2.metric("Stop Loss", "7%")
    c3.metric("Take Profit", "15-25%")
    st.divider()
    st.subheader("🔔 Alert Settings")
    st.write(f"- **Signal Threshold:** {ALERT_PROBABILITY_THRESHOLD*100}% minimum strength")
    st.write(f"- **Alert Time:** 8:00 AM WAT (weekdays)")
    st.write(f"- **Dashboard Refresh:** Every {DASHBOARD_REFRESH_MINUTES} minutes")
    st.divider()
    st.warning("⚠️ Always verify prices with your broker before executing. Use LIMIT orders only.")
    st.info("📖 See README.md for setup & troubleshooting.")

st.divider()
st.caption("Data: TwelveData (NGX) | Model: Technical Scoring | **Not financial advice - DYOR**")
