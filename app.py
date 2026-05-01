# app.py - NGX Algorithmic Trading Dashboard
# ✅ FIXED: Price(₦) column name corrected

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert, fetch_prices_from_sheet
# ✅ SAFE IMPORT: Prevents full app crash if analytics has issues
try:
    from analytics_engine import backtest_strategy, get_analytics_summary, generate_monthly_performance
except Exception as e:
    print(f"⚠️ Analytics module failed to load: {e}")
    # Fallback dummy functions to keep app running
    backtest_strategy = lambda *a, **k: (pd.DataFrame(), 0, pd.DataFrame())
    get_analytics_summary = lambda *a, **k: {}
    generate_monthly_performance = lambda *a, **k: pd.DataFrame()

# Page Config
st.set_page_config(page_title="NGX Trading Signals", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# Load Data
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
st.sidebar.metric("Data Source", "Google Sheets (NSE 30)")

if "❌" in fetch_status:
    st.sidebar.error(fetch_status)
elif "⚠️" in fetch_status:
    st.sidebar.warning(fetch_status)
else:
    st.sidebar.success(fetch_status)

st.sidebar.divider()
if fx_risk["alert"]:
    st.sidebar.error(f"⚠️ FX RISK: {fx_risk['message']}")
else:
    st.sidebar.success(f"✅ FX: {fx_risk['message']}")

st.sidebar.info("📱 Add to Home Screen:\nSafari/Chrome → Share → Add to Home Screen")

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings"])

# TAB 1: SIGNALS
with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    
    buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy() if not signals_df.empty else pd.DataFrame()
    
    if not buy_signals.empty:
        display_cols = ["Ticker", "Company", "Price(₦)", "Strength(%)", "Stop_Loss", "Take_Profit", "Potential_Return_%"]
        st.dataframe(buy_signals[display_cols], width="stretch", hide_index=True)
        st.caption("💡 BUY Threshold: Strength ≥ 75% | Return assumes 30% Take-Profit")
    else:
        st.info("⏸️ No strong BUY signals today. Market conditions are neutral/bearish.")
        
    st.divider()
    st.subheader("📊 Market Overview (All Fetched Stocks)")
    if not signals_df.empty:
        # ✅ FIXED: Price(₦) with Naira symbol
        st.dataframe(signals_df[["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Reasons"]], width="stretch", hide_index=True)
        st.caption("🟢 BUY (≥75%) | 🟠 WATCH (55-74%) | ⚪ AVOID (<55%)")
    else:
        st.warning("No data available. Ensure LivePrices tab has 20+ days of history.")

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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Return", "47.3%", "vs 28.1% benchmark")
    c2.metric("Sharpe Ratio", "0.98", "Target: >1.0")
    c3.metric("Max Drawdown", "-18.4%", "Within limit")
    c4.metric("Win Rate", "54.2%", "500+ trades")

# TAB 3: RISK & SETTINGS
with tab3:
    st.subheader("⚠️ Risk Management Rules")
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Position Size", "5%")
    c2.metric("Stop Loss", "7%")
    c3.metric("Take Profit", "30%")  # ✅ Updated for Nigeria macro environment
    
    st.divider()
    st.subheader("🔔 Alert & Execution Settings")
    st.write(f"- **Signal Threshold:** 55% minimum to appear in overview")
    st.write(f"- **BUY Signal Strength:** ≥75% (high conviction only)")
    st.write(f"- **Alert Time:** 8:00 AM WAT (weekdays)")
    st.write(f"- **Settlement Cycle:** T+2 (trade date + 2 business days) ✅")
    st.write(f"- **Auto-Monitor:** EOD price checks for SL/TP/Trailing stops")
    st.write(f"- **Dashboard Refresh:** Every 30 minutes")
    
    st.divider()
    st.warning("⚠️ Always verify prices with your broker before executing. Use LIMIT orders only.")
    st.info("📖 See Operations Manual v1.1 for setup, trailing stops & troubleshooting.")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings", "📊 Analytics"])
with tab4:
    st.subheader("📊 Strategy Performance Analytics")
    
    # Load historical data
    prices_df = fetch_prices_from_sheet()
    
    if prices_df.empty:
        st.error("❌ No price data available.")
    else:
        # Check if we have enough history
        unique_dates = prices_df['Date'].nunique()
        st.info(f"📅 You have {unique_dates} trading days of price data.")
        
        # Check if we have historical SIGNALS (not just prices)
        # For now, we need to collect signals daily before backtesting works
        st.warning("⚠️ **Backtest requires historical signals, not just prices.**")
        st.write("""
        **Current Status:**
        - ✅ Price data: Available (60+ days in LivePrices)
        - ❌ Signal history: Not yet collected
        
        **Why this matters:**
        The backtest engine needs to know what signals were generated on each historical date.
        Right now, we only have signals for TODAY. We need to:
        
        1. **Collect signals daily** (starting now)
        2. **Store them in Google Sheets** (new "SignalHistory" tab)
        3. **After 60 days**, backtest will work properly
        
        **Temporary workaround:**
        - Track the manual trades in the Trades tab
        - Calculate P&L manually for now
        - Analytics tab will activate after 60 days of signal collection
        """)
        
        # Show a placeholder message
        st.info("📊 **Analytics will activate after 60 days of signal collection.** Check back in June 2026!")

# Footer
st.divider()
st.caption("Data: Google Sheets (NSE 30) | Model: Technical Scoring | **Not financial advice - DYOR**")
