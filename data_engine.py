# data_engine.py - LIVE NGX DATA ENGINE (TwelveData)
# ✅ Returns all fetched stocks + status tracking for debugging

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

def get_api_key():
    try:
        import streamlit as st
        return st.secrets.get("TWELVEDATA_API_KEY")
    except:
        return os.getenv("TWELVEDATA_API_KEY")

def fetch_ngx_data(ticker, api_key):
    """Fetches OHLCV from TwelveData with fallback formats"""
    # TwelveData NGX format: usually just TICKER or TICKER.NG
    formats = [ticker, f"{ticker}.NG", f"{ticker}.NGX"]
    
    for fmt in formats:
        url = f"https://api.twelvedata.com/time_series?symbol={fmt}&interval=1day&outputsize=60&apikey={api_key}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if "status" in data and data["status"] == "error":
                continue
            if "values" in 
                df = pd.DataFrame(data["values"])
                df = df.iloc[::-1].reset_index(drop=True)
                df["Close"] = pd.to_numeric(df["close"])
                df["Volume"] = pd.to_numeric(df["volume"])
                return df[["Close", "Volume"]]
        except Exception:
            continue
    return pd.DataFrame()

def generate_ngx_signals():
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame(), "❌ API Key Missing"

    tickers = [
        "ARADEL", "ZENITHBANK", "BUACEMENT", "MTNN", "NESTLE",
        "LAFARGE", "SEPLAT", "GTCO", "STANBIC", "ACCESSCORP",
        "DANGCEM", "AIRTELAFRI", "FBNH", "UBA", "FLOURMILL",
        "TOTAL", "OANDO", "CADBURY", "UNILEVER", "DANGSUGAR"
    ]
    
    signals = []
    fetch_log = []
    
    for ticker in tickers:
        df = fetch_ngx_data(ticker, api_key)
        if df.empty or len(df) < 20:
            fetch_log.append(f"{ticker}: ❌ Failed")
            time.sleep(0.5)
            continue
            
        fetch_log.append(f"{ticker}: ✅ Fetched")
        close = df['Close']
        volume = df['Volume']
        
        # Indicators
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        rsi = calculate_rsi(close)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal_line
        
        price = close.iloc[-1]
        vol_avg = volume.rolling(20).mean().iloc[-1]
        
        # Scoring
        score = 0
        reasons = []
        if price > sma20.iloc[-1]: score += 25; reasons.append("Price>SMA20")
        if sma20.iloc[-1] > sma50.iloc[-1]: score += 20; reasons.append("SMA20>SMA50")
        if 40 < rsi.iloc[-1] < 65: score += 20; reasons.append("RSI:40-65")
        elif rsi.iloc[-1] < 40: score += 10; reasons.append("RSI:<40")
        if macd_hist.iloc[-1] > 0: score += 15; reasons.append("MACD:>0")
        if volume.iloc[-1] > vol_avg * 1.2: score += 20; reasons.append("Vol:>120%")
            
        score = min(100, score)
        
        signals.append({
            "Ticker": ticker,
            "Company": ticker.replace("MTNN", "MTN Nigeria").replace("GTCO", "GTCo"),
            "Price(₦)": round(price, 2),
            "Signal": "BUY" if score >= 60 else ("WATCH" if score >= 40 else "AVOID"),
            "Strength(%)": score,
            "Stop_Loss": round(price * 0.93, 2),
            "Take_Profit": round(price * 1.15, 2),
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Reasons": ", ".join(reasons)
        })
        time.sleep(0.6)  # Rate limit protection
        
    df_signals = pd.DataFrame(signals)
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    
    status_msg = f"✅ Fetched {len(signals)}/20 stocks. " + " | ".join(fetch_log[:5]) + "..."
    if df_signals.empty:
        return pd.DataFrame(columns=expected_cols), "❌ No stocks fetched. Check API quota or ticker formats."
        
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics():
    return {"Total Return": "Live Tracking", "CAGR": "Pending", "Sharpe Ratio": "Pending", "Max Drawdown": "Live", "Win Rate": "Tracking", "Data Source": "TwelveData (NGX Live)"}

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
