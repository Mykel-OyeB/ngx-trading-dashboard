# alerts.py - TELEGRAM + EMAIL ALERTS
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert(message):
    """Send to Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ Telegram credentials missing")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=15)
        print("✅ Telegram alert sent")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def send_email_alert(subject, html_body):
    """Send to Email (Gmail)"""
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")
    if not email_user or not email_pass:
        print("⚠️ Email credentials missing")
        return
    try:
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_user
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print("✅ Email alert sent")
    except Exception as e:
        print(f"❌ Email error: {e}")

def run_alerts():
    print("🚀 Generating NGX Alerts...")
    signals_df = generate_ngx_signals()
    fx_risk = get_fx_risk_alert()
    
    # Build message
    title = f"🇳🇬 NGX SIGNALS - {datetime.now().strftime('%b %d, %Y')}"
    telegram_msg = f"*{title}*\n\n"
    email_html = f"<h2>{title}</h2>"
    
    if signals_df.empty:
        telegram_msg += "⏸️ No signals meet threshold today."
        email_html += "<p>No signals meet threshold today.</p>"
    else:
        for _, row in signals_df.head(5).iterrows():
            line = f"• *{row['Ticker']}* ₦{row['Price(₦)']} | {row['Strength(%)']}%\n"
            telegram_msg += line
            email_html += f"<p><b>{row['Ticker']}</b> ₦{row['Price(₦)']} | {row['Strength(%)']}%<br>SL: ₦{row['Stop_Loss']} | TP: ₦{row['Take_Profit']}</p>"
            
    if fx_risk["alert"]:
        warn = f"\n⚠️ FX RISK: {fx_risk['message']}"
        telegram_msg += warn
        email_html += f"<p style='color:red'>{warn}</p>"
        
    telegram_msg += "\n📊 Dashboard: [Your Streamlit URL]"
    email_html += "<br><a href='[Your Streamlit URL]'>View Live Dashboard</a>"
    
    send_telegram_alert(telegram_msg)
    send_email_alert(title, email_html)

if __name__ == "__main__":
    run_alerts()
