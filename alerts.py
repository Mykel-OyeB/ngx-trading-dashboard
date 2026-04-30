# alerts.py - TELEGRAM + EMAIL ALERTS
# ✅ Fixed: Proper timing logs, error handling, non-blank messages

import requests
import os
from datetime import datetime
import pytz
from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert(message):
    """Send to Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Telegram credentials missing")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        response = requests.post(url, json={
            "chat_id": chat_id, 
            "text": message, 
            "parse_mode": "Markdown"
        }, timeout=15)
        
        if response.json().get("ok"):
            print("✅ Telegram alert sent successfully")
            return True
        else:
            print(f"❌ Telegram error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

def send_email_alert(subject, html_body):
    """Send to Email (Gmail)"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")
    
    if not email_user or not email_pass:
        print("⚠️ Email credentials missing - skipping email")
        return False
        
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
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def run_alerts():
    """Main alert function"""
    # Log start time
    lagos_tz = pytz.timezone('Africa/Lagos')
    start_time = datetime.now(lagos_tz)
    print(f"🚀 Workflow started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
    
    try:
        print("📊 Fetching NGX signals...")
        signals_df, status_msg = generate_ngx_signals()
        
        print(f"📈 Signals fetched: {len(signals_df)} stocks")
        print(f"📋 Status: {status_msg}")
        
        fx_risk = get_fx_risk_alert()
        
        # Build message
        today = datetime.now().strftime("%B %d, %Y")
        title = f"🇳🇬 *NGX SIGNALS - {today}*"
        
        # Get BUY signals only
        buy_signals = signals_df[signals_df["Signal"] == "BUY"] if not signals_df.empty else None
        
        if buy_signals is None or buy_signals.empty:
            message = f"{title}\n\n"
            message += "⏸️ *No BUY signals meet threshold today.*\n\n"
            message += "📊 Market conditions are neutral/bearish.\n"
            message += "💡 Stay patient for high-conviction setups (≥75% strength).\n\n"
            message += f"ℹ️ {status_msg}"
        else:
            message = f"{title}\n\n"
            message += f" *Top {min(5, len(buy_signals))} BUY Signals:*\n\n"
            
            for _, row in buy_signals.head(5).iterrows():
                ticker = row['Ticker']
                price = row['Price(₦)']
                strength = row['Strength(%)']
                sl = row['Stop_Loss']
                tp = row['Take_Profit']
                ret = row['Potential_Return_%']
                
                message += f"🟢 *{ticker}*\n"
                message += f"   💰 Price: ₦{price:,.2f}\n"
                message += f"   📊 Strength: {strength}%\n"
                message += f"   🎯 TP: ₦{tp:,.2f} (+{ret}%)\n"
                message += f"   🛑 SL: ₦{sl:,.2f} (-7%)\n\n"
            
            if len(buy_signals) > 5:
                message += f" and {len(buy_signals) - 5} more signals\n\n"
        
        # Add FX warning if applicable
        if fx_risk["alert"]:
            message += f"\n⚠️ *FX ALERT:* {fx_risk['message']}\n"
        else:
            message += f"\n✅ *FX Status:* {fx_risk['message']}\n"
        
        # Add dashboard link
        message += "\n📊 *Dashboard:* https://ngx-trading-dashboard.streamlit.app"
        message += "\n\n⏰ *Sent at:* " + datetime.now(lagos_tz).strftime("%H:%M WAT")
        
        # Send alerts
        print("\n📤 Sending Telegram alert...")
        print(f"📝 Message length: {len(message)} characters")
        print(f"📄 Message preview:\n{message[:200]}...")
        
        telegram_success = send_telegram_alert(message)
        
        # Also send email (optional)
        html_body = message.replace("*", "**").replace("\n", "<br>")
        send_email_alert(f"NGX Signals - {today}", html_body)
        
        # Log end time
        end_time = datetime.now(lagos_tz)
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Alert sent at: {end_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
        print(f"⏱️ Total execution time: {duration:.1f} seconds")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error alert
        error_msg = f"🚨 *NGX Bot Error*\n\n"
        error_msg += f"⏰ Time: {datetime.now(lagos_tz).strftime('%Y-%m-%d %H:%M:%S')} WAT\n"
        error_msg += f"❌ Error: {str(e)}\n\n"
        error_msg += "Please check GitHub Actions logs for details."
        
        send_telegram_alert(error_msg)

if __name__ == "__main__":
    run_alerts()
