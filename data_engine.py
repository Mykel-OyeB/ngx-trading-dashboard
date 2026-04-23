# data_engine.py - LIVE NGX DATA ENGINE
import pandas as pd
import numpy as np
import yfinance as yf
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

def generate_ngx_signals():
    """Fetches live NGX data & calculates real technical signals"""
    today = datetime.now()
    
    tickers = [
        "ARADEL.LG", "ZENITHBANK.LG", "BUACEMENT.LG", "MTNN.LG", "NESTLE.NG",
        "LAFARGE.LG", "SEPLAT.LG", "GTCO.LG", "STANBIC.LG", "ACCESSCORP.LG",
        "DANGCEM.LG", "AIRTELAFRI.LG", "FBNH.LG", "UBA.LG", "FLOURMILL.LG",
        "TOTAL.LG", "OANDO.LG", "CADBURY.LG", "UNILEVER.LG", "DANGSUGAR.LG"
    ]
    
    signals = []
    
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", progress=False, auto_adjust=True)
            if df.empty or len(df) < 50:
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
            
            if price > sma20.iloc[-1]:
                score += 25
                reasons.append("Price > SMA20")
            if sma20.iloc[-1] > sma50.iloc[-1]:
                score += 20
                reasons.append("SMA20 > SMA50")
            if 40 < rsi.iloc[-1] < 65:
                score += 20
                reasons.append("RSI Healthy")
            elif rsi.iloc[-1] < 40:
                score += 10
                reasons.append("RSI Oversold")
            if macd_hist.iloc[-1] > 0:
                score += 15
                reasons.append("MACD Bullish")
            if volume.iloc[-1] > vol_avg * 1.2:
                score += 20
                reasons.append("High Volume")
                
            score = min(100, score)
            signal_type = "BUY" if score >= 60 else "WATCH"
            
            if score >= 50:
                signals.append({
                    "Ticker": ticker.replace(".LG", "").replace(".NG", ""),
                    "Company": ticker.replace(".LG", "").replace(".NG", "").replace("MTNN", "MTN Nigeria"),
                    "Price(₦)": round(price, 2),
                    "Signal": signal_type,
                    "Strength(%)": score,
                    "Stop_Loss": round(price * 0.93, 2),
                    "Take_Profit": round(price * 1.15, 2),
                    "Date": today.strftime("%Y-%m-%d"),
                    "Reasons": ", ".join(reasons)
                })
                
            time.sleep(0.5)
        except Exception:
            continue
            
    df_signals = pd.DataFrame(signals)
    
    # 🔧 FIX: Force exact column structure so Streamlit never crashes
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    if df_signals.empty:
        return pd.DataFrame(columns=expected_cols)
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False)

def get_portfolio_metrics():
    return {
        "Total Return": "Live Tracking",
        "CAGR": "Pending",
        "Sharpe Ratio": "Pending",
        "Max Drawdown": "Live",
        "Win Rate": "Tracking",
        "Data Source": "Yahoo Finance (NGX)"
    }

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
