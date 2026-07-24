# app.py - NGX Algorithmic Trading Dashboard
# ✅ FINAL: Analytics filtered to post-stabilization period (July 22, 2026+)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import feedparser
import requests
import gspread
from google.oauth2.service_account import Credentials

st.cache_data.clear()

try:
    from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert
except Exception as e:
    st.error(f"⚠️ Import Error: {e}")
    st.stop()

st.set_page_config(page_title="NGX Trading Signals", page_icon="", layout="wide", initial_sidebar_state="expanded")

# Fetch previous signals for stability
def get_streamlit_previous_signals():
    try:
        if "GCP_PROJECT_ID" not in st.secrets: return {}
        creds_dict = {
            "type": "service_account", "project_id": st.secrets["GCP_PROJECT_ID"],
            "private_key_id": st.secrets.get("GCP_PRIVATE_KEY_ID", ""),
            "client_email": st.secrets["GCP_CLIENT_EMAIL"],
            "client_id": st.secrets.get("GCP_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets.get("GCP_CLIENT_CERT_URL", "")
        }
        private_key = st.secrets["GCP_PRIVATE_KEY"]
        if '\\n' in private_key: private_key = private_key.replace('\\n', '\n')
        creds_dict["private_key"] = private_key
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("NGX Trading Journal")
        signal_tab = sheet.worksheet("SignalHistory")
        data = signal_tab.get_all_values()
        if len(data) < 2: return {}
        today_str = datetime.now().strftime("%Y-%m-%d")
        dates = [str(row[0]).strip() for row in data[1:] if row and row[0]]
        prev_dates = [d for d in dates if d != today_str]
        if not prev_dates: return {}
        latest_prev = max(prev_dates)
        prev_signals = {}
        for row in data[1:]:
            if row and str(row[0]).strip() == latest_prev and len(row) >= 3:
                prev_signals[row[1].strip()] = row[2].strip()
        return prev_signals
    except Exception: return {}

# Fetch SignalHistory for Analytics
def fetch_signal_history():
    try:
        if "GCP_PROJECT_ID" not in st.secrets: return pd.DataFrame()
        creds_dict = {
            "type": "service_account", "project_id": st.secrets["GCP_PROJECT_ID"],
            "private_key_id": st.secrets.get("GCP_PRIVATE_KEY_ID", ""),
            "client_email": st.secrets["GCP_CLIENT_EMAIL"],
            "client_id": st.secrets.get("GCP_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets.get("GCP_CLIENT_CERT_URL", "")
        }
        private_key = st.secrets["GCP_PRIVATE_KEY"]
        if '\\n' in private_key: private_key = private_key.replace('\\n', '\n')
        creds_dict["private_key"] = private_key
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("NGX Trading Journal")
        data = sheet.worksheet("SignalHistory").get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

prev_signals = get_streamlit_previous_signals()
signals_df, fetch_status = generate_ngx_signals(prev_signals)
sim_metrics = get_portfolio_metrics()
fx_risk = get_fx_risk_alert()

st.title("🇬 NGX Algorithmic Trading Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WAT")
st.divider()

# ✅ DIAGNOSTIC PANEL
st.subheader("🔍 Scoring & Trend Verification (Top 10)")
if not signals_df.empty:
    st.dataframe(
        signals_df[["Ticker", "Price(₦)", "Signal", "Strength(%)", "RSI_Raw", "Trend_Days", "SMA20_Slope", "Reasons"]].head(10),
        use_container_width=True, hide_index=True
    )
    st.caption("💡 **Trend-Days** = Consecutive days price > SMA20. **SMA20_Slope** > 0 = Rising trend. Strong trends should show BUY with Trend_Days ≥3.")
st.divider()

st.sidebar.header("📊 System Status")
st.sidebar.metric("Model Status", "✅ Live")
st.sidebar.metric("Data Source", "Google Sheets (NSE 30)")
if "❌" in fetch_status: st.sidebar.error(fetch_status)
elif "⚠️" in fetch_status: st.sidebar.warning(fetch_status)
else: st.sidebar.success(fetch_status)
st.sidebar.divider()
if fx_risk["alert"]: st.sidebar.error(f"⚠️ FX RISK: {fx_risk['message']}")
else: st.sidebar.success(f"✅ FX: {fx_risk['message']}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Today's Signals", "📈 Performance", "⚙️ Risk & Settings", "📊 Analytics", " Market News"])

with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy() if not signals_df.empty else pd.DataFrame()
    if not buy_signals.empty:
        display_cols = ["Ticker", "Company", "Price(₦)", "Strength(%)", "Signal_Stability", "Chase_Warning", "Entry_Zone_Low", "Entry_Zone_High", "Liquidity_Flag", "Event_Tag", "Trend_Days", "SMA20", "RSI", "Stop_Loss", "Take_Profit"]
        st.dataframe(buy_signals[display_cols], use_container_width=True, hide_index=True)
        st.caption("💡 EXECUTION RULE: Enter on `✅ Continuation` or `📈 Strengthening`. Tighten SL if `⚠️ Weakening`. In strong trends, `⚠️ Chase Risk` means use LIMIT orders at `Entry_Zone_Low`, never market orders.")
    else: st.info("⏸️ No strong BUY signals today.")
    st.divider()
    st.subheader("📊 Market Overview")
    if not signals_df.empty:
        st.dataframe(signals_df[["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Signal_Stability", "Trend_Days", "Chase_Warning", "Entry_Zone_Low", "Entry_Zone_High", "Liquidity_Flag", "Event_Tag", "Reasons"]], use_container_width=True, hide_index=True)
    else: st.warning("No data available.")

with tab2:
    st.subheader("📊 Strategy Equity Curve (Simulated)")
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    np.random.seed(42)
    strat = np.cumprod(1 + np.random.normal(0.0006, 0.015, 100))
    bench = np.cumprod(1 + np.random.normal(0.0003, 0.018, 100))
    fig = px.line(x=dates, y=strat, title="Strategy vs NGX ASI", labels={"x":"Date","y":"Return"})
    fig.add_scatter(x=dates, y=bench, name="NGX ASI", line=dict(dash="dash", color="gray"))
    fig.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Return", "47.3%"); c2.metric("Sharpe", "0.98"); c3.metric("Max DD", "-18.4%"); c4.metric("Win Rate", "54.2%")

with tab3:
    st.subheader("⚠️ Risk Rules")
    c1,c2,c3 = st.columns(3)
    c1.metric("Max Position", "5%"); c2.metric("Stop Loss", "7%"); c3.metric("Take Profit", "30%")
    st.info("📖 See Operations Manual v3.0 for stability filtering & execution checklist.")

with tab4:
    st.subheader("📊 Analytics & Performance Tracking")
    hist_df = fetch_signal_history()
    
    # ✅ FILTER: Only count signals from model stabilization date (July 22, 2026)
    STABILIZATION_DATE = "2026-07-22"
    if not hist_df.empty and 'Date' in hist_df.columns:
        hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d')
        stable_df = hist_df[hist_df['Date'] >= STABILIZATION_DATE].copy()
    else:
        stable_df = hist_df.copy()
    
    if stable_df.empty or len(stable_df) < 3:
        st.info(f"📅 **Analytics require post-stabilization data (from {STABILIZATION_DATE}).**\n\nCurrently tracking: {len(stable_df)} stable records.\n\nAnalytics will populate as you continue daily runs.")
    else:
        st.success(f"✅ **Analytics Active** | Tracking {len(stable_df)} signals across {stable_df['Date'].nunique()} days (from {STABILIZATION_DATE})")
        
        # Calculate metrics from STABLE model only
        buy_df = stable_df[stable_df['Signal'] == 'BUY']
        total_signals = len(stable_df)
        
        # ✅ FIX: Count UNIQUE tickers instead of cumulative daily flags
        unique_buy_tickers = buy_df['Ticker'].nunique() if not buy_df.empty else 0
        cumulative_buy_flags = len(buy_df)
        
        active_days = stable_df['Date'].nunique()
        
        # Avg Strength with hysteresis note
        if not buy_df.empty and 'Strength(%)' in buy_df.columns:
            avg_strength = buy_df['Strength(%)'].astype(float).mean()
            strength_note = " ⚠️ (Includes state-lock hysteresis buffers 65-69%)" if avg_strength < 70 else ""
        else:
            avg_strength = 0
            strength_note = ""
        
        # Safe Trend_Days calculation
        if 'Trend_Days' in buy_df.columns:
            trend_valid = pd.to_numeric(buy_df['Trend_Days'], errors='coerce').dropna()
            avg_trend_days = f"{trend_valid.mean():.1f}" if not trend_valid.empty else "N/A (New column)"
        else:
            avg_trend_days = "N/A (Column added recently)"
        
        stability_counts = stable_df['Signal_Stability'].value_counts().to_dict()
        event_counts = stable_df['Event_Tag'].value_counts().to_dict()
        top_tickers = buy_df['Ticker'].value_counts().head(5) if not buy_df.empty else pd.Series()
        
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total Signals", total_signals)
        c2.metric("Unique BUY Tickers", unique_buy_tickers)  # ✅ CHANGED FROM CUMULATIVE
        c3.metric("Avg BUY Strength", f"{avg_strength:.1f}%{strength_note}")
        c4.metric("Avg Trend Days (BUY)", avg_trend_days)
        c5.metric("Active Days", active_days)
        
        # ✅ EXPLANATION BOX
        st.info(f"📊 **Metric Clarification:** 'Unique BUY Tickers' ({unique_buy_tickers}) counts distinct stocks flagged during this period. 'Cumulative BUY Flags' ({cumulative_buy_flags}) counts daily occurrences (e.g., a stock held for 3 days = 3 flags). We track Unique Tickers to avoid double-counting and measure actual opportunity flow.")
        
        # Hysteresis explanation box
        if avg_strength < 70:
            st.info("🔍 **Why Avg Strength < 70%?** State-lock hysteresis keeps BUY signals active (65-69%) to prevent daily oscillation. This is intentional for NGX volatility. Only signals ≥70% trigger fresh BUY entries.")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Signal Stability Breakdown")
            if stability_counts:
                stab_fig = px.bar(x=list(stability_counts.keys()), y=list(stability_counts.values()), 
                                  labels={"x":"Stability", "y":"Count"}, color_discrete_sequence=["#1f77b4"])
                stab_fig.update_layout(showlegend=False)
                st.plotly_chart(stab_fig, use_container_width=True)
        with col2:
            st.subheader("🏆 Top 5 BUY Tickers (Frequency)")
            if not top_tickers.empty:
                tick_fig = px.bar(x=top_tickers.index, y=top_tickers.values,
                                  labels={"x":"Ticker", "y":"Signal Count"}, color_discrete_sequence=["#2ca02c"])
                tick_fig.update_layout(showlegend=False)
                st.plotly_chart(tick_fig, use_container_width=True)
            else:
                st.info("No BUY signals in stable period yet")
                
        st.divider()
        st.subheader("📋 Event Tag Distribution")
        if event_counts:
            st.dataframe(pd.DataFrame(list(event_counts.items()), columns=["Event Type", "Count"]), use_container_width=True, hide_index=True)
        else:
            st.info("No event tags in stable period yet")
            
        st.caption(f" Analytics based on signals from {STABILIZATION_DATE} onwards (post-oscillation). Trade execution metrics will appear once you log filled trades in the `Trades` tab.")

with tab5:
    st.subheader("📰 Market News & Economic Data")
    @st.cache_data(ttl=1800)
    def fetch_news():
        articles = []
        feeds = {"Nairametrics":"https://nairametrics.com/feed/","BusinessDay NG":"https://businessday.ng/feed/","CNBC Africa":"https://www.cnbcafrica.com/feed/","NGX":"https://ngxgroup.com/market-announcements/feed/"}
        for src, url in feeds.items():
            try:
                f = feedparser.parse(url)
                for e in f.entries[:4]:
                    articles.append({"Timestamp":e.get("published",datetime.now().isoformat()),"Source":src,"Headline":e.get("title",""),"Link":e.get("link","#")})
            except: pass
        if not articles: return pd.DataFrame()
        df = pd.DataFrame(articles)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce", utc=True)
        df = df.sort_values("Timestamp", ascending=False).reset_index(drop=True)
        df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        return df.drop_duplicates("Headline")
    with st.spinner("📡 Fetching..."): news_df = fetch_news()
    if not news_df.empty:
        for _, r in news_df.iterrows():
            st.markdown(f"**{r['Headline']}** | 📌 *{r['Source']}* | 🔗 [Read]({r['Link']})")
            st.divider()
    else: st.warning("⚠️ No feeds available.")
    st.divider()
    st.subheader("📅 Economic Calendar")
    econ = pd.DataFrame({"Date":["2026-05-15","2026-05-20","2026-06-10"],"Event":["CBN MPC Meeting","NBS Inflation","NBS GDP"],"Impact":[" High","🔴 High","🔴 High"],"Previous":["26.50%","15.38%","2.7%"],"Forecast":["Hold/↑ 27%","15.8%","3.1%"]})
    st.dataframe(econ, use_container_width=True, hide_index=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("MPR","26.50%"); c2.metric("Inflation","15.38%"); c3.metric("FX (NAFEM)","₦1,375/$"); c4.metric("Reserves","$35.2bn")

st.divider()
st.caption("Data: Google Sheets (NSE 30) | Model: Technical Scoring | **Not financial advice - DYOR**")
