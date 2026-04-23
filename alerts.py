# alerts.py
# Automated Telegram Alert System
# Runs daily at 8:00 AM WAT via GitHub Actions

import requests
from datetime import datetime
from data_engine import generate_ngx_signals, get_fx_risk_alert
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_PROBABILITY_THRESHOLD

def send_telegram_alert():
    """Send daily NGX trading signals to Telegram"""
    
    # Check if configured
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  ERROR: Telegram bot token not configured!")
        print("Please add your TELEGRAM_BOT_TOKEN to GitHub Secrets")
        return
    
    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("⚠️  ERROR: Telegram chat ID not configured!")
        print("Please add your TELEGRAM_CHAT_ID to GitHub Secrets")
        return
    
    # Generate signals
    signals_df = generate_ngx_signals()
    fx_risk = get_fx_risk_alert()
    
    # Filter high-conviction buy signals
    buy_signals = signals_df[
        (signals_df["Signal"] == "BUY") & 
        (signals_df["Strength(%)"] >= ALERT_PROBABILITY_THRESHOLD * 100)
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
    
    # Add dashboard link (replace with your actual Streamlit URL)
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += "📊 *View Full Dashboard:*\n"
    message += "https://your-username-ngx-trading-dashboard.streamlit.app\n\n"
    message += "⚡ *Quick Actions:*\n"
    message += "• Use LIMIT orders only\n"
    message += "• Max 5% position size\n"
    message += "• Set hard stop-loss at -7%\n"
    message += "• Scale out at +15%, +20%, +25%\n\n"
    message += "_Model: XGBoost Classifier | Threshold: 55%_"
    
    # Send to Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
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
        print("Check your internet connection and Telegram bot settings")

# Run the alert
if __name__ == "__main__":
    print("🚀 Starting NGX Daily Alert System...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    send_telegram_alert()
