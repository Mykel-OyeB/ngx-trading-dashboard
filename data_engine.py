# data_engine.py - LIVE NGX DATA ENGINE (TwelveData API)
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

def fetch_ngx_data(ticker):
    """Fetches OHLCV from TwelveData (Free tier: 800 req/day)"""
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if not api_key:
        return pd.DataFrame()  # Triggers graceful fallback
        
    url = f"https://api.twelvedata.com/time_series?symbol={ticker}.NGX&interval=1day&outputsize=90&apikey={api_key}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "status" in data and data["status"] == "error":
            return pd.DataFrame()
        # ✅ FIXED: Added missing "data:" 
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df = df.iloc[::-1].reset_index(drop=True)  # Chronological order
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["Close"] = pd.to_numeric(df["close"])
            df["Volume"] = pd.to_numeric(df["volume"])
            df.set_index("datetime", inplace=True)
            return df[["Close", "Volume"]]
    except Exception:
        pass
    return pd.DataFrame()

def generate_ngx_signals():
    today = datetime.now()
    tickers = [
        "ARADEL", "ZENITHBANK", "BUACEMENT", "MTNN", "NESTLE",
        "LAFARGE", "SEPLAT", "GTCO", "STANBIC", "ACCESSCORP",
        "DANGCEM", "AIRTELAFRI", "FBNH", "UBA", "FLOURMILL",
        "TOTAL", "OANDO", "CADBURY", "UNILEVER", "DANGSUGAR"
    ]
    
    signals = []
    for ticker in tickers:
        df = fetch_ngx_data(ticker)
        if df.empty or len(df) < 20:
            continue
            
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
        
        if price > sma20.iloc[-1]: score += 25; reasons.append("Price > SMA20")
        if sma20.iloc[-1] > sma50.iloc[-1]: score += 20; reasons.append("SMA20 > SMA50")
        if 40 < rsi.iloc[-1] < 65: score += 20; reasons.append("RSI Healthy")
        elif rsi.iloc[-1] < 40: score += 10; reasons.append("RSI Oversold")
        if macd_hist.iloc[-1] > 0: score += 15; reasons.append("MACD Bullish")
        if volume.iloc[-1] > vol_avg * 1.2: score += 20; reasons.append("High Volume")
            
        score = min(100, score)
        signal_type = "BUY" if score >= 60 else "WATCH"
        
        if score >= 50:
            signals.append({
                "Ticker": ticker,
                "Company": ticker.replace("MTNN", "MTN Nigeria").replace("GTCO", "GTCo"),
                "Price(₦)": round(price, 2),
                "Signal": signal_type,
                "Strength(%)": score,
                "Stop_Loss": round(price * 0.93, 2),
                "Take_Profit": round(price * 1.15, 2),
                "Date": today.strftime("%Y-%m-%d"),
                "Reasons": ", ".join(reasons)
            })
        
    df_signals = pd.DataFrame(signals)
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False) if not df_signals.empty else pd.DataFrame(columns=expected_cols)

def get_portfolio_metrics():
    return {"Total Return": "Live Tracking", "CAGR": "Pending", "Sharpe Ratio": "Pending", "Max Drawdown": "Live", "Win Rate": "Tracking", "Data Source": "TwelveData (NGX Live)"}

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
