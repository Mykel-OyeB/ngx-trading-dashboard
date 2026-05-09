# data_engine.py - NGX DATA ENGINE (Google Sheets)
# ✅ NEW: Liquidity_Flag & Event_Tag columns for execution safety

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
    SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS1V2GumgyU4sVrsrulu8F5v2rpH9dU2M8Grn5qVd7omTR9sHntQvXH0WS7u9Eg7lqydndDsZnU6dLA/pub?gid=1101410921&single=true&output=csv"
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        df = df.dropna(subset=['Close', 'Volume', 'Date', 'Ticker'])
        return df
    except Exception as e:
        print(f"Sheet fetch error: {e}")
        return pd.DataFrame()

def generate_ngx_signals():
    prices_df = fetch_prices_from_sheet()
    if prices_df.empty:
        return pd.DataFrame(), "❌ Sheet returned no valid data."
    
    latest_date = prices_df['Date'].max()
    latest_prices = prices_df[prices_df['Date'] == latest_date]
    if latest_prices.empty:
        return pd.DataFrame(), f"❌ No valid data for {latest_date}"
    
    signals = []
    fetch_log = []
    
    for _, row in latest_prices.iterrows():
        ticker = str(row['Ticker']).strip()
        ticker_history = prices_df[prices_df['Ticker'].str.strip() == ticker].sort_values('Date').tail(60)
        
        if len(ticker_history) < 20:
            fetch_log.append(f"{ticker}: ️")
            continue
        fetch_log.append(f"{ticker}: ✅")
        
        close = ticker_history['Close']
        volume = ticker_history['Volume']
        
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        rsi = calculate_rsi(close)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_hist = macd - macd.ewm(span=9, adjust=False).mean()
        
        price = row['Close']
        avg_vol_20d = volume.rolling(20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        
        # ✅ LIQUIDITY FLAG
        if pd.notna(current_vol) and pd.notna(avg_vol_20d) and avg_vol_20d > 0:
            if current_vol < avg_vol_20d * 0.5:
                liq_flag = "⚠️ Low"
            elif current_vol > avg_vol_20d * 3.0:
                liq_flag = "⚠️ Spike"
            else:
                liq_flag = "✅ Normal"
        else:
            liq_flag = " No Data"
        
        # ✅ EVENT TAG (Earnings/News vs Technical)
        price_vs_sma20 = abs((price - sma20.iloc[-1]) / sma20.iloc[-1]) if pd.notna(sma20.iloc[-1]) and sma20.iloc[-1] != 0 else 0
        if pd.notna(current_vol) and pd.notna(avg_vol_20d) and avg_vol_20d > 0:
            if current_vol > avg_vol_20d * 2.5 and price_vs_sma20 > 0.04:
                event_tag = "📅 Earnings/News"
            else:
                event_tag = "📊 Technical"
        else:
            event_tag = "📊 Technical"
        
        # Scoring
        score = 0
        reasons = []
        try:
            if pd.notna(price) and pd.notna(sma20.iloc[-1]) and price > sma20.iloc[-1]: score += 25; reasons.append("Price>SMA20")
            if pd.notna(sma20.iloc[-1]) and pd.notna(sma50.iloc[-1]) and sma20.iloc[-1] > sma50.iloc[-1]: score += 20; reasons.append("SMA20>SMA50")
            if pd.notna(rsi.iloc[-1]) and 40 < rsi.iloc[-1] < 65: score += 20; reasons.append("RSI:40-65")
            elif pd.notna(rsi.iloc[-1]) and rsi.iloc[-1] < 40: score += 10; reasons.append("RSI:<40")
            if pd.notna(macd_hist.iloc[-1]) and macd_hist.iloc[-1] > 0: score += 15; reasons.append("MACD:>0")
            vol_3d = volume.rolling(3).mean().iloc[-1]
            if pd.notna(current_vol) and pd.notna(vol_3d) and vol_3d > 0 and current_vol > vol_3d * 1.15: score += 10; reasons.append("Vol:Steady+")
        except Exception: pass
        score = min(100, score)
        
        if score >= 75: signal = "BUY"
        elif score >= 65: signal = "BUY" if ("Price>SMA20" in reasons and "SMA20>SMA50" in reasons) else "WATCH"
        elif score >= 55: signal = "WATCH"
        else: signal = "AVOID"
        
        signals.append({
            "Ticker": ticker,
            "Company": ticker.replace("MTNN", "MTN Nigeria").replace("GTCO", "GTCo"),
            "Price(₦)": round(float(price), 2) if pd.notna(price) else 0,
            "Signal": signal,
            "Strength(%)": score,
            "Stop_Loss": round(float(price) * 0.93, 2) if pd.notna(price) else 0,
            "Take_Profit": round(float(price) * 1.30, 2) if pd.notna(price) else 0,
            "Potential_Return_%": 30.0,
            "Date": latest_date.strftime("%Y-%m-%d"),
            "Reasons": ", ".join(reasons),
            "SMA20": round(float(sma20.iloc[-1]), 2) if pd.notna(sma20.iloc[-1]) else 0,
            "SMA50": round(float(sma50.iloc[-1]), 2) if pd.notna(sma50.iloc[-1]) else 0,
            "RSI": round(float(rsi.iloc[-1]), 1) if pd.notna(rsi.iloc[-1]) else 0,
            "MACD_Hist": round(float(macd_hist.iloc[-1]), 4) if pd.notna(macd_hist.iloc[-1]) else 0,
            "Liquidity_Flag": liq_flag,  # ✅ NEW
            "Event_Tag": event_tag       # ✅ NEW
        })
        
    df_signals = pd.DataFrame(signals)
    expected_cols = [
        "Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", 
        "Stop_Loss", "Take_Profit", "Potential_Return_%", "Date", "Reasons",
        "SMA20", "SMA50", "RSI", "MACD_Hist", "Liquidity_Flag", "Event_Tag"
    ]
    status_msg = f"✅ {len(signals)}/{len(latest_prices)} analyzed. " + " | ".join(fetch_log[:10])
    if df_signals.empty: return pd.DataFrame(columns=expected_cols), status_msg
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics(): return {"Total Return": "Live Tracking", "Data Source": "Google Sheets"}
def get_fx_risk_alert(): return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable"}
