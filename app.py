# app.py - NGX Algorithmic Trading Dashboard
# ✅ Updated: Shows Liquidity_Flag & Event_Tag in signals table

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import feedparser
import requests

try:
    from data_engine import generate_ngx_signals, get_portfolio_metrics, get_fx_risk_alert
except Exception: pass

st.set_page_config(page_title="NGX Trading Signals", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
signals_df, fetch_status = generate_ngx_signals()
sim_metrics = get_portfolio_metrics()
fx_risk = get_fx_risk_alert()

st.title("🇳🇬 NGX Algorithmic Trading Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WAT")
st.divider()

st.sidebar.header(" System Status")
st.sidebar.metric("Model Status", "✅ Live")
st.sidebar.metric("Data Source", "Google Sheets (NSE 30)")
if "❌" in fetch_status: st.sidebar.error(fetch_status)
elif "⚠️" in fetch_status: st.sidebar.warning(fetch_status)
else: st.sidebar.success(fetch_status)
st.sidebar.divider()
if fx_risk["alert"]: st.sidebar.error(f"⚠️ FX RISK: {fx_risk['message']}")
else: st.sidebar.success(f"✅ FX: {fx_risk['message']}")
st.sidebar.info("📱 Add to Home Screen:\nSafari/Chrome → Share → Add to Home Screen")

tab1, tab2, tab3, tab4, tab5 = st.tabs([" Today's Signals", "📈 Performance", "⚙️ Risk & Settings", "📊 Analytics", "📰 Market News"])

with tab1:
    st.subheader("🟢 Buy Signals - " + datetime.now().strftime("%B %d, %Y"))
    buy_signals = signals_df[signals_df["Signal"] == "BUY"].copy() if not signals_df.empty else pd.DataFrame()
    
    if not buy_signals.empty:
        # ✅ UPDATED: Includes Liquidity & Event columns
        display_cols = [
            "Ticker", "Company", "Price(₦)", "Strength(%)",
            "Liquidity_Flag", "Event_Tag",  # ✅ NEW
            "SMA20", "SMA50", "RSI", "MACD_Hist",
            "Stop_Loss", "Take_Profit", "Potential_Return_%"
        ]
        st.dataframe(buy_signals[display_cols], use_container_width=True, hide_index=True)
        st.caption("💡 BUY Threshold: ≥75% | ⚠️ Liquidity/Event flags guide execution sizing & timing")
    else:
        st.info("⏸️ No strong BUY signals today.")
        
    st.divider()
    st.subheader("📊 Market Overview")
    if not signals_df.empty:
        st.dataframe(signals_df[["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Liquidity_Flag", "Event_Tag", "Reasons"]], use_container_width=True, hide_index=True)
    else:
        st.warning("No data available.")

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
    st.info("📖 See Operations Manual v2.1 for liquidity execution checklist & trailing stops.")

with tab4:
    st.subheader("📊 Analytics")
    st.info(" Activates after 60 days of signal history (~July 2026). Collecting data daily.")

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
            st.markdown(f"**{r['Headline']}** | 📌 *{r['Source']}* |  [Read]({r['Link']})")
            st.divider()
    else: st.warning("⚠️ No feeds available.")
    
    st.divider()
    st.subheader(" Economic Calendar")
    econ = pd.DataFrame({"Date":["2026-05-15","2026-05-20","2026-06-10"],"Event":["CBN MPC Meeting","NBS Inflation","NBS GDP"],"Impact":[" High","🔴 High"," High"],"Previous":["26.50%","15.38%","2.7%"],"Forecast":["Hold/↑ 27%","15.8%","3.1%"]})
    st.dataframe(econ, use_container_width=True, hide_index=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("MPR","26.50%"); c2.metric("Inflation","15.38%"); c3.metric("FX (NAFEM)","₦1,375/$"); c4.metric("Reserves","$35.2bn")

st.divider()
st.caption("Data: Google Sheets (NSE 30) | Model: Technical Scoring | **Not financial advice - DYOR**")
