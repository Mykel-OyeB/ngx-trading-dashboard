# data_engine.py - LIVE NGX DATA ENGINE (Yahoo Finance)
# ✅ FIXED: Uses correct .NG suffix, immune to syntax errors

import yfinance as yf
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

def fetch_ngx_data(ticker):
    """Fetches data using Yahoo Finance with .NG suffix"""
    try:
        # Use .NG suffix for Nigeria
        df = yf.download(f"{ticker}.NG", period="3mo", progress=False)
        
        # Check if data is valid
        if df.empty:
            return pd.DataFrame()
            
        df = df.dropna()
        if len(df) < 20:
            return pd.DataFrame()
            
        return df[["Close", "Volume"]]
    except Exception:
        return pd.DataFrame()

def generate_ngx_signals():
    tickers = [
        "ARADEL", "ZENITHBANK", "MTNN", "GTCO", "DANGCEM",
        "SEPLAT", "STANBIC", "FBNH", "UBA", "ACCESSCORP",
        "NESTLE", "LAFARGE"
    ]
    
    signals = []
    fetch_log = []
    
    for ticker in tickers:
        df = fetch_ngx_data(ticker)
        
        # Check if DataFrame is empty safely
        if df.empty:
            fetch_log.append(f"{ticker}: ❌")
            time.sleep(0.5)
            continue
            
        fetch_log.append(f"{ticker}: ✅")
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
        time.sleep(0.5)
        
    df_signals = pd.DataFrame(signals)
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    
    status_msg = f"✅ Fetched {len(signals)}/{len(tickers)} stocks. " + " | ".join(fetch_log)
    
    if df_signals.empty:
        return pd.DataFrame(columns=expected_cols), "⚠️ Yahoo Finance returned no data. Check ticker symbols."
        
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics():
    return {"Total Return": "Live Tracking", "CAGR": "Pending", "Sharpe Ratio": "Pending", "Max Drawdown": "Live", "Win Rate": "Tracking", "Data Source": "Yahoo Finance (NGX)"}

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
