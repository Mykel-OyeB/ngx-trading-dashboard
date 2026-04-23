# alerts.py
# ✅ FIXED: Now reads Telegram credentials from GitHub Secrets (environment variables)

import requests
import os  # ← Added to read environment variables
from datetime import datetime
from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert():
    """Send daily NGX trading signals to Telegram"""
    
    # ✅ Read from GitHub Secrets (environment variables) FIRST
    # Fallback to config.py only for local testing
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # If not in environment, try config.py (for local testing)
    if not BOT_TOKEN or not CHAT_ID:
        try:
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            BOT_TOKEN = BOT_TOKEN if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else None
            CHAT_ID = CHAT_ID if CHAT_ID != "YOUR_CHAT_ID_HERE" else None
        except:
            pass
    
    # Final check
    if not BOT_TOKEN:
        print("⚠️  ERROR: Telegram bot token not configured!")
        print("Please add TELEGRAM_BOT_TOKEN to GitHub Secrets")
        return
    
    if not CHAT_ID:
        print("⚠️  ERROR: Telegram chat ID not configured!")
        print("Please add TELEGRAM_CHAT_ID to GitHub Secrets")
        return
    
    # Generate signals
    signals_df = generate_ngx_signals()
    fx_risk = get_fx_risk_alert()
    
    # Filter high-conviction buy signals
    ALERT_THRESHOLD = 0.55  # 55% minimum strength
    buy_signals = signals_df[
        (signals_df["Signal"] == "BUY") & 
        (signals_df["Strength(%)"] >= ALERT_THRESHOLD * 100)
    ].sort_values("Strength(%)", ascending=False)
    
    # Build alert message
    message = f"""🇳🇬 *NGX DAILY TRADING SIGNALS*
📅 {datetime.now().strftime('%A, %B %d, %Y')}
⏰ {datetime.now().strftime('%H:%M')} WAT

━━━━━━━━━━━━━━━━━━━━
"""
    
    # Add buy signals
    if len(buy_signals) > 0:
        message += "🟢 *TOP BUY SIGNALS:*\n\n"
        
        for idx, (_, row) in enumerate(buy_signals.head(5).iterrows(), 1):
            message += f"{idx}. *{row['Ticker']}* - {row['Company']}\n"
            message += f"   💰 Entry: ₦{row['Price(₦)']:,.2f}\n"
            message += f"   📊 Strength: {row['Strength(%)']}%\n"
            message += f"   🛑 Stop: ₦{row['Stop_Loss']:,.2f}\n"
            message += f"   🎯 Target: ₦{row['Take_Profit']:,.2f}\n\n"
    else:
        message += "⏸️ *No high-conviction buy signals today*\n\n"
        message += "Market conditions don't meet our criteria.\n"
        message += "Stay patient and preserve capital.\n\n"
    
    # Add FX risk warning
    if fx_risk["alert"]:
        message += "⚠️ *FX RISK ALERT*\n"
        message += f"{fx_risk['message']}\n"
        message += "Consider reducing equity exposure by 20%.\n\n"
    
    # Add dashboard link
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += "📊 *View Full Dashboard:*\n"
    message += "https://your-app.streamlit.app\n\n"
    message += "⚡ *Quick Actions:*\n"
    message += "• Use LIMIT orders only\n"
    message += "• Max 5% position size\n"
    message += "• Set hard stop-loss at -7%\n"
    message += "• Scale out at +15%, +20%, +25%\n\n"
    message += "_Model: XGBoost Classifier | Threshold: 55%_"
    
    # Send to Telegram
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ Alert sent successfully to Telegram!")
            print(f"Sent {len(buy_signals)} buy signals")
        else:
            print(f"❌ Telegram API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send alert: {e}")

# Run the alert
if __name__ == "__main__":
    print("🚀 Starting NGX Daily Alert System...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    send_telegram_alert()
