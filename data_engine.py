# data_engine.py - NGX DATA ENGINE (Google Sheets)
# ✅ REFINED: NGX-aware Event_Tag logic + all Day 1 validations preserved

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

def generate_ngx_signals(previous_signals=None):
    prices_df = fetch_prices_from_sheet()
    if prices_df.empty:
        return pd.DataFrame(), "❌ Sheet returned no valid data."
    
    latest_date = prices_df['Date'].max()
    latest_prices = prices_df[prices_df['Date'] == latest_date]
    if latest_prices.empty:
        return pd.DataFrame(), f"❌ No valid data for {latest_date}"
    
    signals = []
    fetch_log = []
    strength_map = {"AVOID": 0, "WATCH": 1, "BUY": 2}
    
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
        
        price = float(row['Close']) if pd.notna(row['Close']) else 0
        avg_vol_20d = volume.rolling(20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        
        # ✅ TREND PERSISTENCE
        above_sma20 = close > sma20
        trend_days = 0
        for i in range(len(above_sma20)-1, -1, -1):
            if above_sma20.iloc[i]: trend_days += 1
            else: break
        trend_days = min(trend_days, 20)
        
        # ✅ SMA SLOPE
        sma20_slope = sma20.iloc[-1] - sma20.iloc[-5] if len(sma20) >= 5 else 0
        
        # ✅ LIQUIDITY FLAG
        if pd.notna(current_vol) and pd.notna(avg_vol_20d) and avg_vol_20d > 0:
            if current_vol < avg_vol_20d * 0.5: liq_flag = "⚠️ Low"
            elif current_vol > avg_vol_20d * 3.0: liq_flag = "⚠️ Spike"
            else: liq_flag = "✅ Normal"
        else: liq_flag = "⚠️ No Data"
        
        # ✅ NGX-AWARE EVENT TAG (Refined for earnings/news reality)
        rsi_val = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 0
        price_vs_sma20 = abs((price - sma20.iloc[-1]) / sma20.iloc[-1]) if pd.notna(sma20.iloc[-1]) and sma20.iloc[-1] != 0 else 0
        vol_ratio = current_vol / avg_vol_20d if pd.notna(current_vol) and pd.notna(avg_vol_20d) and avg_vol_20d > 0 else 0
        
        # NGX earnings often show: moderate volume + sustained momentum + RSI in trend zone
        vol_trigger = vol_ratio >= 1.8
        momentum_trigger = price_vs_sma20 > 0.03 or (rsi_val > 60 and pd.notna(macd_hist.iloc[-1]) and macd_hist.iloc[-1] > 0)
        
        if vol_trigger and momentum_trigger:
            event_tag = "📅 Earnings/News"
        else:
            event_tag = "📊 Technical"
        
        # ✅ NGX-AWARE SCORING (Unchanged from Day 1 validation)
        score = 0
        reasons = []
        
        # 1. Trend Structure (30 pts)
        if pd.notna(sma20.iloc[-1]) and price > sma20.iloc[-1]: score += 15; reasons.append("Price>SMA20")
        if pd.notna(sma20.iloc[-1]) and pd.notna(sma50.iloc[-1]) and sma20.iloc[-1] > sma50.iloc[-1]: score += 15; reasons.append("SMA20>SMA50")
            
        # 2. Trend Persistence & Slope (20 pts)
        if trend_days >= 3: score += 10; reasons.append(f"Trend:{trend_days}d")
        if sma20_slope > 0: score += 10; reasons.append("SMA20:Rising")
            
        # 3. Momentum (RSI + MACD) (25 pts)
        if 50 <= rsi_val <= 75: score += 15; reasons.append("RSI:Trend-Zone")
        elif 75 < rsi_val <= 85: score += 10; reasons.append("RSI:Strong")
        elif rsi_val > 85: score += 5; reasons.append("RSI:Extended")
        elif rsi_val < 50: score += 5; reasons.append("RSI:Cooling")
            
        if pd.notna(macd_hist.iloc[-1]) and macd_hist.iloc[-1] > 0: score += 10; reasons.append("MACD:>0")
            
        # 4. Volume/Confirmation (10 pts)
        if vol_ratio >= 1.0: score += 10; reasons.append("Vol:High-Interest")
        elif vol_ratio >= 0.5: score += 5; reasons.append("Vol:Active")
        elif vol_ratio < 0.5 and trend_days >= 3: score += 5; reasons.append("Vol:Bid-Driven")
            
        # 5. Trend Alignment Bonus (5 pts)
        if all(r in reasons for r in ["Price>SMA20", "SMA20>SMA50", "MACD:>0", "SMA20:Rising"]):
            score += 5; reasons.append("Trend:Aligned")
            
        score = min(100, score)
        
        # ✅ STATE-LOCK HYSTERESIS (Unchanged)
        prev_signal = previous_signals.get(ticker, "") if previous_signals else ""
        if prev_signal == "BUY":
            if price < sma20.iloc[-1] or score < 45:
                signal = "AVOID" if score < 35 else "WATCH"
            else:
                signal = "BUY"
        else:
            if score >= 70: signal = "BUY"
            elif score >= 55: signal = "WATCH"
            else: signal = "AVOID"
        
        # ✅ SMART ENTRY ZONES (Unchanged)
        if pd.notna(sma20.iloc[-1]) and sma20.iloc[-1] > 0:
            buffer = 0.015
            entry_low = round(sma20.iloc[-1] * (1 - buffer), 2)
            entry_high = round(sma20.iloc[-1] * (1 + buffer), 2)
            prev_close = float(close.iloc[-2]) if len(close) >= 2 and pd.notna(close.iloc[-2]) else price
            gap_pct = abs((price - prev_close) / prev_close) if prev_close != 0 else 0
            chase_warning = "⚠️ Chase Risk" if (price > entry_high or gap_pct > 0.03) else "✅ Fair Zone"
            pullback_watch = "🔍 Pullback/Zone" if (signal == "BUY" and chase_warning == "✅ Fair Zone") else ""
        else:
            entry_low = entry_high = 0
            chase_warning = "⚠️ No Data"
            pullback_watch = ""
        
        # ✅ SIGNAL STABILITY (Unchanged)
        today_val = strength_map.get(signal, 0)
        prev_val = strength_map.get(prev_signal, -1)
        
        if prev_val == -1: stability = "🆕 New Signal"
        elif today_val == prev_val: stability = "✅ Continuation"
        elif today_val > prev_val: stability = "📈 Strengthening"
        else: stability = "⚠️ Weakening"
        
        company_name = (
            ticker.replace("MTNN", "MTN Nigeria")
                  .replace("GTCO", "GTCo")
                  .replace("WAPCO", "HBM Nigeria")
                  .replace("HBMNG", "HBM Nigeria")
        )
        
        signals.append({
            "Ticker": ticker, "Company": company_name, "Price(₦)": round(price, 2),
            "Signal": signal, "Strength(%)": score, "RSI_Raw": round(rsi_val, 1),
            "Trend_Days": trend_days, "SMA20_Slope": round(sma20_slope, 2),
            "Stop_Loss": round(price * 0.93, 2), "Take_Profit": round(price * 1.30, 2),
            "Potential_Return_%": 30.0, "Date": latest_date.strftime("%Y-%m-%d"),
            "Reasons": ", ".join(reasons), "SMA20": round(float(sma20.iloc[-1]), 2),
            "SMA50": round(float(sma50.iloc[-1]), 2), "RSI": round(rsi_val, 1),
            "MACD_Hist": round(float(macd_hist.iloc[-1]), 4), "Liquidity_Flag": liq_flag,
            "Event_Tag": event_tag, "Entry_Zone_Low": entry_low, "Entry_Zone_High": entry_high,
            "Chase_Warning": chase_warning, "Pullback_Watch": pullback_watch,
            "Signal_Stability": stability
        })
        
    df_signals = pd.DataFrame(signals)
    expected_cols = [
        "Ticker", "Company", "Price(₦)", "Signal", "Strength(%)", "RSI_Raw", "Trend_Days", "SMA20_Slope",
        "Stop_Loss", "Take_Profit", "Potential_Return_%", "Date", "Reasons",
        "SMA20", "SMA50", "RSI", "MACD_Hist", "Liquidity_Flag", "Event_Tag",
        "Entry_Zone_Low", "Entry_Zone_High", "Chase_Warning", "Pullback_Watch",
        "Signal_Stability"
    ]
    status_msg = f"✅ {len(signals)}/{len(latest_prices)} analyzed. " + " | ".join(fetch_log[:10])
    if df_signals.empty: return pd.DataFrame(columns=expected_cols), status_msg
    return df_signals[expected_cols].sort_values("Strength(%)", ascending=False), status_msg

def get_portfolio_metrics(): return {"Total Return": "Live Tracking", "Data Source": "Google Sheets"}
def get_fx_risk_alert(): return {"change_pct": 0.012, "alert": False, "message": "USD/NGN stable"}
