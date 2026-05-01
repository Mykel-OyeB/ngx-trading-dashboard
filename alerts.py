# alerts.py - TELEGRAM + GOOGLE SHEETS LOGGING
# ✅ Auto-logs all signals to SignalHistory tab daily

import requests
import os
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("❌ Telegram credentials missing")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=15)
        if response.json().get("ok"):
            print("✅ Telegram alert sent successfully")
            return True
        else:
            print(f"❌ Telegram error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

def log_signals_to_sheet(signals_df, date_str):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = {
            "type": "service_account",
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GCP_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("GCP_CLIENT_EMAIL"),
            "client_id": os.getenv("GCP_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("GCP_CLIENT_CERT_URL")
        }
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("NGX Trading Journal")
        signal_tab = sheet.worksheet("SignalHistory")
        
        rows_to_add = []
        for _, row in signals_df.iterrows():
            rows_to_add.append([
                date_str, row['Ticker'], row['Signal'], row['Strength(%)'],
                row['Price(₦)'], row['Stop_Loss'], row['Take_Profit'], row['Reasons']
            ])
        
        if rows_to_add:
            signal_tab.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"✅ Logged {len(rows_to_add)} signals to Google Sheets")
            return True
        return False
    except Exception as e:
        print(f" Google Sheets logging error: {e}")
        return False

def run_alerts():
    lagos_tz = pytz.timezone('Africa/Lagos')
    start_time = datetime.now(lagos_tz)
    print(f"🚀 Workflow started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
    try:
        print("📊 Fetching NGX signals...")
        signals_df, status_msg = generate_ngx_signals()
        print(f"📈 Signals fetched: {len(signals_df)} stocks")
        fx_risk = get_fx_risk_alert()
        
        today = datetime.now().strftime("%B %d, %Y")
        title = f"🇬 *NGX SIGNALS - {today}*"
        buy_signals = signals_df[signals_df["Signal"] == "BUY"] if not signals_df.empty else None
        
        if buy_signals is None or buy_signals.empty:
            message = f"{title}\n\n⏸️ *No BUY signals meet threshold today.*\n\n📊 Market conditions are neutral/bearish.\n💡 Stay patient for high-conviction setups (≥75% strength).\n\nℹ️ {status_msg}"
        else:
            message = f"{title}\n\n🎯 *Top {min(5, len(buy_signals))} BUY Signals:*\n\n"
            for _, row in buy_signals.head(5).iterrows():
                message += f" *{row['Ticker']}*\n   💰 Price: ₦{row['Price()']:,.2f}\n   📊 Strength: {row['Strength(%)']}%\n   🎯 TP: ₦{row['Take_Profit']:,.2f} (+30%)\n   🛑 SL: ₦{row['Stop_Loss']:,.2f} (-7%)\n\n"
            if len(buy_signals) > 5:
                message += f" and {len(buy_signals) - 5} more signals\n\n"
        
        if fx_risk["alert"]:
            message += f"\n⚠️ *FX ALERT:* {fx_risk['message']}\n"
        else:
            message += f"\n✅ *FX Status:* {fx_risk['message']}\n"
        message += "\n📊 *Dashboard:* https://ngx-trading-dashboard.streamlit.app"
        message += "\n\n⏰ *Sent at:* " + datetime.now(lagos_tz).strftime("%H:%M WAT")
        
        print("\n📤 Sending Telegram alert...")
        send_telegram_alert(message)
        
        print("\n📝 Logging signals to Google Sheets...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_signals_to_sheet(signals_df, date_str)
        
        end_time = datetime.now(lagos_tz)
        print(f"\n✅ Alert sent at: {end_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
        print(f"️ Total execution time: {(end_time - start_time).total_seconds():.1f} seconds")
    except Exception as e:
        print(f" CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_alerts()
