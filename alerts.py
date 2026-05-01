# alerts.py - DEBUG VERSION
import requests
import os
from datetime import datetime
import pytz

print("🚀 Starting alerts.py...")

try:
    import gspread
    from google.oauth2.service_account import Credentials
    print("✅ Google libraries imported successfully")
except Exception as e:
    print(f"❌ Failed to import Google libraries: {e}")
    print("💡 Check requirements.txt has gspread and google-auth")

from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in secrets")
        return False
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found in secrets")
        return False
        
    print(f"📤 Sending to Telegram (token: {token[:10]}..., chat: {chat_id})")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={
            "chat_id": chat_id, 
            "text": message, 
            "parse_mode": "Markdown"
        }, timeout=15)
        
        result = response.json()
        print(f"📱 Telegram response: {result}")
        
        if result.get("ok"):
            print("✅ Telegram alert sent successfully")
            return True
        else:
            print(f"❌ Telegram error: {result}")
            return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

def log_signals_to_sheet(signals_df, date_str):
    print("📝 Attempting to log to Google Sheets...")
    
    try:
        # Check if secrets exist
        required_secrets = ['GCP_PROJECT_ID', 'GCP_PRIVATE_KEY_ID', 'GCP_PRIVATE_KEY', 
                           'GCP_CLIENT_EMAIL', 'GCP_CLIENT_ID', 'GCP_CLIENT_CERT_URL']
        
        for secret in required_secrets:
            if not os.getenv(secret):
                print(f"❌ Secret missing: {secret}")
                return False
            else:
                print(f"✅ Secret found: {secret}")
        
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
        
        print("🔑 Attempting to authorize with Google...")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ Google authorization successful")
        
        # Try to open sheet
        sheet_name = "NGX Trading Journal"
        print(f"📂 Opening sheet: '{sheet_name}'...")
        sheet = client.open(sheet_name)
        print("✅ Sheet opened successfully")
        
        # Try to access SignalHistory tab
        print("📑 Accessing SignalHistory tab...")
        signal_tab = sheet.worksheet("SignalHistory")
        print("✅ SignalHistory tab found")
        
        # Prepare data
        rows_to_add = []
        for _, row in signals_df.iterrows():
            rows_to_add.append([
                date_str, row['Ticker'], row['Signal'], row['Strength(%)'],
                row['Price(₦)'], row['Stop_Loss'], row['Take_Profit'], row['Reasons']
            ])
        
        print(f"📊 Preparing to append {len(rows_to_add)} rows...")
        
        if rows_to_add:
            signal_tab.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"✅ Successfully logged {len(rows_to_add)} signals to Google Sheets")
            return True
        else:
            print("⚠️ No signals to log")
            return False
            
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ ERROR: Spreadsheet 'NGX Trading Journal' not found")
        print("💡 Check the exact sheet name matches")
        return False
    except gspread.exceptions.WorksheetNotFound:
        print("❌ ERROR: Worksheet 'SignalHistory' not found")
        print("💡 Create a tab named exactly 'SignalHistory'")
        return False
    except gspread.exceptions.NotAuthorized:
        print("❌ ERROR: Not authorized to access sheet")
        print("💡 Share the sheet with the service account email")
        return False
    except Exception as e:
        print(f"❌ Google Sheets error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_alerts():
    lagos_tz = pytz.timezone('Africa/Lagos')
    start_time = datetime.now(lagos_tz)
    print(f"🚀 Workflow started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
    
    try:
        print("📊 Fetching NGX signals...")
        signals_df, status_msg = generate_ngx_signals()
        
        if signals_df.empty:
            print("⚠️ No signals generated")
        else:
            print(f"📈 Generated {len(signals_df)} signals")
            print(f"📋 Status message: {status_msg}")
        
        fx_risk = get_fx_risk_alert()
        
        # Build Telegram message
        today = datetime.now().strftime("%B %d, %Y")
        title = f"🇳 *NGX SIGNALS - {today}*"
        
        buy_signals = signals_df[signals_df["Signal"] == "BUY"] if not signals_df.empty else None
        
        if buy_signals is None or buy_signals.empty:
            message = f"{title}\n\n⏸️ *No BUY signals meet threshold today.*\n\n📊 Market conditions are neutral/bearish.\n💡 Stay patient for high-conviction setups (≥75% strength).\n\nℹ️ {status_msg}"
        else:
            message = f"{title}\n\n🎯 *Top {min(5, len(buy_signals))} BUY Signals:*\n\n"
            for _, row in buy_signals.head(5).iterrows():
                message += f"🟢 *{row['Ticker']}*\n"
                message += f"   💰 Price: ₦{row['Price(₦)']:,.2f}\n"
                message += f"   📊 Strength: {row['Strength(%)']}%\n"
                message += f"   🎯 TP: {row['Take_Profit']:,.2f} (+30%)\n"
                message += f"   🛑 SL: {row['Stop_Loss']:,.2f} (-7%)\n\n"
            if len(buy_signals) > 5:
                message += f" and {len(buy_signals) - 5} more signals\n\n"
        
        if fx_risk["alert"]:
            message += f"\n⚠️ *FX ALERT:* {fx_risk['message']}\n"
        else:
            message += f"\n✅ *FX Status:* {fx_risk['message']}\n"
        
        message += "\n📊 *Dashboard:* https://ngx-trading-dashboard.streamlit.app"
        message += "\n\n⏰ *Sent at:* " + datetime.now(lagos_tz).strftime("%H:%M WAT")
        
        print("\n" + "="*50)
        print("📱 TELEGRAM MESSAGE PREVIEW:")
        print(message[:200] + "...")
        print("="*50 + "\n")
        
        # Send Telegram
        print("📤 Sending Telegram alert...")
        telegram_success = send_telegram_alert(message)
        
        # Log to Google Sheets
        print("\n📝 Logging to Google Sheets...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        sheet_success = log_signals_to_sheet(signals_df, date_str)
        
        end_time = datetime.now(lagos_tz)
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*50)
        print("✅ WORKFLOW COMPLETE")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        print(f"📱 Telegram: {'✅ Success' if telegram_success else '❌ Failed'}")
        print(f"📊 Sheets: {'✅ Success' if sheet_success else '❌ Failed'}")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_alerts()
