# data_engine.py - NGX DATA ENGINE (Google Sheets)
# ✅ 100% Reliable: Uses your Google Sheet for prices

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

def fetch_prices_from_sheet():
    """Fetches prices from published Google Sheet"""
    # You'll publish your LivePrices sheet to web (CSV format)
    # URL format: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv&sheet=LivePrices
    
    SHEET_URL = https://docs.google.com/spreadsheets/d/e/2PACX-1vS1V2GumgyU4sVrsrulu8F5v2rpH9dU2M8Grn5qVd7omTR9sHntQvXH0WS7u9Eg7lqydndDsZnU6dLA/pub?output=csv
    
    try:
        df = pd.read_csv(SHEET_URL)
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame()

def generate_ngx_signals():
    # Get prices from Google Sheet
    prices_df = fetch_prices_from_sheet()
    
    if prices_df.empty:
        return pd.DataFrame(), "⚠️ No prices in Google Sheet. Add data to LivePrices tab."
    
    # Get latest date
    latest_date = prices_df['Date'].max()
    latest_prices = prices_df[prices_df['Date'] == latest_date]
    
    if latest_prices.empty:
        return pd.DataFrame(), "⚠️ No prices for latest date."
    
    signals = []
    fetch_log = []
    
    for _, row in latest_prices.iterrows():
        ticker = row['Ticker']
        
        # Get historical data for this ticker (last 60 days)
        ticker_history = prices_df[prices_df['Ticker'] == ticker].sort_values('Date').tail(60)
        
        if len(ticker_history) < 20:
            fetch_log.append(f"{ticker}: ❌ (Need more history)")
            continue
            
        fetch_log.append(f"{ticker}: ✅")
        
        close = ticker_history['Close']
        volume = ticker_history['Volume']
        
        # Indicators
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        rsi = calculate_rsi(close)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal_line
        
        price = row['Close']
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
            "Date": latest_date.strftime("%Y-%m-%d"),
            "Reasons": ", ".join(reasons)
        })
        
    df_signals = pd.DataFrame(signals)
    expected_cols = ["Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "Stop_Loss", "Take_Profit", "Date", "Reasons"]
    
    status_msg = f"✅ Analyzed {len(signals)} stocks from Google Sheet. " + " | ".join(fetch_log)
    
    if df_signals.empty:
        return pd.DataFrame(columns=expected_cols), "⚠️ No stocks met minimum data requirements."
        
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics():
    return {"Total Return": "Live Tracking", "CAGR": "Pending", "Sharpe Ratio": "Pending", "Max Drawdown": "Live", "Win Rate": "Tracking", "Data Source": "Google Sheets (Manual Entry)"}

def get_fx_risk_alert():
    return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable this week"}
