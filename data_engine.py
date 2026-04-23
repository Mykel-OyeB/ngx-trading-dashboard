# data_engine.py
import pandas as pd
import numpy as np
from datetime import datetime

def generate_ngx_signals():
    np.random.seed(42)
    today = datetime.now()
    stocks = {
        "ARADEL": {"price": 1679.90, "sector": "Oil & Gas"},
        "ZENITHBANK": {"price": 129.50, "sector": "Banking"},
        "BUACEMENT": {"price": 326.70, "sector": "Industrial"},
        "MTNN": {"price": 820.50, "sector": "Telecoms"},
        "NESTLE": {"price": 3055.50, "sector": "Consumer Goods"},
        "LAFARGE": {"price": 275.00, "sector": "Industrial"},
        "SEPLAT": {"price": 285.40, "sector": "Oil & Gas"},
        "GTCO": {"price": 130.00, "sector": "Banking"},
        "STANBIC": {"price": 133.10, "sector": "Banking"},
        "ACCESSCORP": {"price": 31.00, "sector": "Banking"},
    }
    signals = []
    for ticker, info in stocks.items():
        prob = np.random.uniform(0.45, 0.88)
        signal_type = "BUY" if prob > 0.55 else "HOLD"
        entry = info["price"]
        signals.append({
            "Ticker": ticker,
            "Company": ticker.replace("CORP", "Holdings").replace("MTNN", "MTN Nigeria"),
            "Sector": info["sector"],
            "Price(₦)": entry,
            "Signal": signal_type,
            "Strength(%)": round(prob * 100, 1),
            "Stop_Loss": round(entry * 0.93, 2),
            "Take_Profit": round(entry * 1.15, 2),
            "Date": today.strftime("%Y-%m-%d")
        })
    df = pd.DataFrame(signals).sort_values("Strength(%)", ascending=False)
    return df

def get_portfolio_metrics():
    return {
        "Total Return": "+47.3%",
        "CAGR": "15.8%",
        "Sharpe Ratio": "0.98",
        "Max Drawdown": "-18.4%",
        "Win Rate": "54.2%",
        "Current Value": "₦14,730,000"
    }

def get_fx_risk_alert():
    weekly_change = np.random.uniform(-0.01, 0.04)
    return {"change_pct": weekly_change, "alert": weekly_change > 0.03, "message": f"USD/NGN moved {weekly_change:.1%} this week"}
