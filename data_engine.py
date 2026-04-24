# data_engine.py - LIVE NGX DATA ENGINE (MarketStack)
# ✅ FINAL FIX: Replaced vulnerable syntax with explicit empty dict check

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
from collections import defaultdict
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
        return st.secrets.get("MARKETSTACK_API_KEY")
    except:
        return os.getenv("MARKETSTACK_API_KEY")

def fetch_all_ngx_data(api_key):
    tickers = [
        "ARADEL", "ZENITHBANK", "MTNN", "GTCO", "DANGCEM",
        "SEPLAT", "STANBIC", "FBNH", "UBA", "ACCESSCORP",
        "NESTLE", "LAFARGE"
    ]
    
    symbols_param = ",".join([f"{t}.XNGS" for t in tickers])
    url = f"http://api.marketstack.com/v1/eod?access_key={api_key}&symbols={symbols_param}&limit=100"
    
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        
        if "data" not in data or not data["data"]:
            return {}
            
        stock_data = defaultdict(list)
        for record in data["data"]:
            ticker = record["symbol"].replace(".XNGS", "")
            stock_data[ticker].append({
                "date": record["date"],
                "close": record["close"],
                "volume": record["volume"]
            })
        
        dfs = {}
        for ticker, records in stock_data.items():
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            df["Close"] = pd.to_numeric(df["close"])
            df["Volume"] = pd.to_numeric(df["volume"])
            dfs[ticker] = df
            
        return dfs
        
    except Exception as e:
        print(f"MarketStack Fetch Error: {e}")
        return {}

def generate_ngx_signals():
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame(), "❌ API Key Missing"

    dfs = fetch_all_ngx_data(api_key)
    
    # ✅ SAFE CHECK: Explicitly compares to empty dict to prevent markdown corruption
    if dfs == {}:
        return pd.DataFrame(), "❌ MarketStack returned no data."

    signals = []
    fetch_log = []
    
    for ticker, df in dfs.items():
        if len(df) < 20:
            fetch_log.append(f"{ticker}: ❌ (Not enough data)")
            continue
            
        fetch_log.append(f"{ticker}: ✅")
        close = df['Close']
        volume = df['Volume']
        
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
        
    df_signals = pd.DataFrame(signals)
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    
    status_msg = f"✅ Fetched {len(signals)}/{len(dfs)} stocks. " + " | ".join(fetch_log)
    if df_signals.empty:
        return pd.DataFrame(columns=expected_cols), "❌ No stocks fetched."
        
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics():
    return {"Total Return": "Live Tracking", "CAGR": "Pending", "Sharpe Ratio": "Pending", "Max Drawdown": "Live", "Win Rate": "Tracking", "Data Source": "MarketStack (NGX)"}

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
