# app.py
# NGX Trading Dashboard - Main Streamlit Application
# ✅ FIXED: Added missing numpy import

import streamlit as st
import pandas as pd
import numpy as np  # ← THIS WAS MISSING - NOW ADDED
import plotly.express as px
from datetime import datetime
from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert
from config import DASHBOARD_REFRESH_MINUTES, ALERT_PROBABILITY_THRESHOLD

# Page configuration - Mobile optimized
st.set_page_config(
    page_title="NGX Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh every 30 minutes
st.markdown(f"""
    <meta http-equiv="refresh" content="{DASHBOARD_REFRESH_MINUTES*60}">
""", unsafe_allow_html=True)

# Header
st.title("🇳🇬 NGX Algorithmic Trading Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WAT")
st.divider()

# Load data
signals_df = generate_ngx_signals()
metrics = get_portfolio_metrics()
fx_risk = get_fx_risk_alert()

# Sidebar - Portfolio Summary
st.sidebar.header("📊 Portfolio Performance")
for key, value in metrics.items():
    st.sidebar.metric(key, value)

st.sidebar.divider()

# FX Risk Alert
if fx_risk["alert"]:
    st.sidebar.error(f"⚠️ FX RISK ALERT\n{fx_risk['message']}\n\nConsider reducing exposure by 20%")
else:
    st.sidebar.success(f"✅ FX Status\n{fx_risk['message']}\n\nNormal trading conditions")

st.sidebar.divider()
st.sidebar.info("📱 **Mobile App Setup:**\n\n1. Open in Safari/Chrome\n2. Tap Share icon\n3. 'Add to Home Screen'\n4. Name: NGX Signals")

# Main Content - Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings"])

# TAB 1: LIVE SIGNALS
with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    
    # Filter buy signals
    buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy()
    
    if len(buy_signals) > 0:
        # Display top signals
        st.dataframe(
            buy_signals[["Ticker", "Company", "Price(₦)", "Strength(%)", "Stop_Loss", "Take_Profit"]],
            use_container_width=True,
            hide_index=True
        )
        
        # Highlight strongest signals
        st.caption("💡 **Signal Guide:** Green = Strong (>75%) | Orange = Moderate (60-75%) | Gray = Watch (<60%)")
        
        # Top 3 picks
        st.divider()
        st.subheader("🏆 Top 3 High-Conviction Picks")
        top3 = buy_signals.nlargest(3, "Strength(%)")
        
        col1, col2, col3 = st.columns(3)
        for idx, (_, row) in enumerate(top3.iterrows()):
            with [col1, col2, col3][idx]:
                st.metric(row["Ticker"], f"₦{row['Price(₦)']}", f"{row['Strength(%)']}% Strength")
                st.caption(f"SL: ₦{row['Stop_Loss']} | TP: ₦{row['Take_Profit']}")
    else:
        st.info("⏸️ No buy signals meet the threshold today. Stay patient.")

# TAB 2: PERFORMANCE
with tab2:
    st.subheader("📊 Strategy Equity Curve (2023-2026)")
    
    # Generate mock equity curve for demo
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    np.random.seed(42)  # ✅ Now works because numpy is imported
    strategy_returns = np.cumprod(1 + np.random.normal(0.0006, 0.015, 100))
    benchmark_returns = np.cumprod(1 + np.random.normal(0.0003, 0.018, 100))
    
    fig = px.line(
        x=dates, 
        y=strategy_returns,
        title="Strategy vs NGX All-Share Index",
        labels={"x": "Date", "y": "Cumulative Return"}
    )
    fig.add_scatter(x=dates, y=benchmark_returns, name="NGX ASI Benchmark", 
                    line=dict(dash="dash", color="gray"))
    fig.update_layout(hovermode="x unified", height=500, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.divider()
    st.subheader("📈 Key Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Return", "47.3%", "vs 28.1% benchmark")
    col2.metric("Sharpe Ratio", "0.98", "Target: >1.0")
    col3.metric("Max Drawdown", "-18.4%", "Within limit")
    col4.metric("Win Rate", "54.2%", "500+ trades")

# TAB 3: RISK & SETTINGS
with tab3:
    st.subheader("⚠️ Risk Management Rules")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Max Position Size", "5%", "Per stock")
    col2.metric("Stop Loss", "7%", "Hard stop")
    col3.metric("Take Profit", "15-25%", "Scale out")
    
    st.divider()
    
    st.subheader("🔔 Alert Settings")
    st.write(f"- **Signal Threshold:** {ALERT_PROBABILITY_THRESHOLD*100}% minimum strength")
    st.write(f"- **Alert Time:** 8:00 AM WAT (weekdays)")
    st.write(f"- **Dashboard Refresh:** Every {DASHBOARD_REFRESH_MINUTES} minutes")
    
    st.divider()
    
    st.warning("⚠️ **Important:** This dashboard uses simulated data for demonstration. To connect real NGX data, edit `data_engine.py` with your broker API or NGX Group data feed.")
    
    st.info("📖 **Need Help?** See README.md for setup instructions or contact support.")

# Footer
st.divider()
st.caption("Data: NGX Group | Model: XGBoost Classifier | Last retrained: March 2026 | **Not financial advice - DYOR**")
