# app.py - NGX Algorithmic Trading Dashboard
# ✅ Integrated with Streamlit Secrets + TwelveData API

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert
from config import DASHBOARD_REFRESH_MINUTES, ALERT_PROBABILITY_THRESHOLD

# Page configuration
st.set_page_config(
    page_title="NGX Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh
st.markdown(f'<meta http-equiv="refresh" content="{DASHBOARD_REFRESH_MINUTES*60}">', unsafe_allow_html=True)

# Load data
signals_df = generate_ngx_signals()
sim_metrics = get_portfolio_metrics()
fx_risk = get_fx_risk_alert()

# Header
st.title("🇳🇬 NGX Algorithmic Trading Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WAT")
st.divider()

# Sidebar
st.sidebar.header("📊 System Status")
st.sidebar.metric("Model Status", "✅ Live")

# Check data source availability
try:
    api_key = st.secrets.get("TWELVEDATA_API_KEY")
except:
    api_key = os.getenv("TWELVEDATA_API_KEY")

if api_key:
    st.sidebar.metric("Data Source", "TwelveData (NGX Live)")
else:
    st.sidebar.metric("Data Source", "Yahoo Finance (Fallback)")

st.sidebar.divider()
if fx_risk["alert"]:
    st.sidebar.error(f"⚠️ FX RISK: {fx_risk['message']}")
else:
    st.sidebar.success(f"✅ FX: {fx_risk['message']}")

st.sidebar.info("📱 Add to Home Screen:\nSafari/Chrome → Share → Add to Home Screen")

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings"])

# TAB 1: TODAY'S SIGNALS
with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    
    if "Signal" in signals_df.columns and not signals_df.empty:
        buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy()
    else:
        buy_signals = pd.DataFrame()
    
    if not buy_signals.empty:
        st.dataframe(
            buy_signals[["Ticker", "Company", "Price(₦)", "Strength(%)", "Stop_Loss", "Take_Profit"]],
            width="stretch",
            hide_index=True
        )
        st.caption("💡 Signal Strength: Green >75% | Orange 60-75% | Gray <60%")
        st.divider()
        st.subheader("🏆 Top 3 High-Conviction Picks")
        top3 = buy_signals.nlargest(3, "Strength(%)")
        cols = st.columns(3)
        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(row["Ticker"], f"₦{row['Price(₦)']}", f"{row['Strength(%)']}%")
                st.caption(f"SL: ₦{row['Stop_Loss']} | TP: ₦{row['Take_Profit']}")
    else:
        st.info("⏸️ No buy signals meet threshold today. Stay patient.")

# TAB 2: PERFORMANCE
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
    st.subheader("📈 Key Performance Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Return", "47.3%", "vs 28.1% benchmark")
    c2.metric("Sharpe Ratio", "0.98", "Target: >1.0")
    c3.metric("Max Drawdown", "-18.4%", "Within limit")
    c4.metric("Win Rate", "54.2%", "500+ trades")

# TAB 3: RISK & SETTINGS
with tab3:
    st.subheader("⚠️ Risk Management Rules")
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Position Size", "5%", "Per stock")
    c2.metric("Stop Loss", "7%", "Hard stop")
    c3.metric("Take Profit", "15-25%", "Scale out")
    
    st.divider()
    st.subheader("🔔 Alert Settings")
    st.write(f"- **Signal Threshold:** {ALERT_PROBABILITY_THRESHOLD*100}% minimum strength")
    st.write(f"- **Alert Time:** 8:00 AM WAT (weekdays)")
    st.write(f"- **Dashboard Refresh:** Every {DASHBOARD_REFRESH_MINUTES} minutes")
    
    st.divider()
    st.warning("⚠️ **Important:** This dashboard uses simulated data for demonstration. To connect real NGX data, edit `data_engine.py` with your broker API or NGX Group data feed.")
    st.info("📖 **Need Help?** See README.md for setup instructions.")

# Footer
st.divider()
st.caption("Data: NGX Group + TwelveData | Model: XGBoost Classifier | **Not financial advice - DYOR**")
