# alerts.py - TELEGRAM + GOOGLE SHEETS LOGGING
# ✅ Fixed: Added Drive scope to get_previous_signals() for spreadsheet lookup

import requests
import os
from datetime import datetime, timedelta
import pytz
import gspread
from google.oauth2.service_account import Credentials
from data_engine import generate_ngx_signals, get_fx_risk_alert

def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=15)
        return r.json().get("ok")
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_previous_signals():
    """Fetches yesterday's signals from SignalHistory tab with robust matching"""
    try:
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
        # ✅ FIXED: Added Drive scope for spreadsheet lookup by name
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("NGX Trading Journal")
        signal_tab = sheet.worksheet("SignalHistory")
        
        # Get all data, skip header
        data = signal_tab.get_all_values()
        if len(data) < 2: 
            print("⚠️ SignalHistory has <2 rows. Cannot fetch previous signals.")
            return {}
        
        # Calculate yesterday's date in YYYY-MM-DD
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"🔍 Looking for signals dated: {yesterday}")
        
        prev_signals = {}
        match_count = 0
        
        for row in data[1:]:
            if not row or len(row) < 3: continue
            
            # Robust date matching: strip spaces, check exact match or contains
            cell_date = str(row[0]).strip()
            if cell_date == yesterday or yesterday in cell_date:
                ticker = str(row[1]).strip()
                signal = str(row[2]).strip()
                if ticker and signal:
                    prev_signals[ticker] = signal
                    match_count += 1
                    
        print(f"✅ Found {match_count} signals for {yesterday}")
        if match_count == 0:
            print(f"   Tip: Check SignalHistory Column A. Dates should be YYYY-MM-DD (e.g., {yesterday})")
            
        return prev_signals
    except Exception as e:
        print(f"⚠️ get_previous_signals failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def log_signals_to_sheet(signals_df, date_str):
    """Append signals with automatic deduplication"""
    try:
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
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("NGX Trading Journal")
        signal_tab = sheet.worksheet("SignalHistory")
        
        # ✅ DEDUPLICATION: Remove today's existing rows
        all_values = signal_tab.get_all_values()
        rows_to_delete = []
        for i, row in enumerate(all_values):
            if row and str(row[0]).strip() == date_str:
                rows_to_delete.append(i + 1)
        
        if rows_to_delete:
            for row_num in sorted(rows_to_delete, reverse=True):
                signal_tab.delete_rows(row_num)
            print(f"🗑️ Cleared {len(rows_to_delete)} duplicate rows for {date_str}")
        
        # ✅ APPEND FRESH DATA
        rows_to_add = []
        for _, row in signals_df.iterrows():
            rows_to_add.append([
                date_str, row['Ticker'], row['Signal'], row['Strength(%)'],
                row['Price(₦)'], row['Stop_Loss'], row['Take_Profit'], row['Reasons'],
                row['SMA20'], row['SMA50'], row['RSI'], row['MACD_Hist'],
                row['Liquidity_Flag'], row['Event_Tag'],
                row['Entry_Zone_Low'], row['Entry_Zone_High'],
                row['Chase_Warning'], row['Pullback_Watch'],
                row['Signal_Stability']
            ])
        
        if rows_to_add:
            signal_tab.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"✅ Logged {len(rows_to_add)} signals to Google Sheets")
            return True
        return False
    except Exception as e:
        print(f"❌ Sheets error: {e}")
        return False

def run_alerts():
    lagos_tz = pytz.timezone('Africa/Lagos')
    start_time = datetime.now(lagos_tz)
    print(f"🚀 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
    try:
        # ✅ Fetch previous signals for stability tracking
        prev_signals = get_previous_signals()
        signals_df, status_msg = generate_ngx_signals(prev_signals)
        print(f"📈 Generated {len(signals_df)} signals")
        
        fx_risk = get_fx_risk_alert()
        today = datetime.now().strftime("%B %d, %Y")
        title = f"🇳🇬 *NGX SIGNALS - {today}*"
        buy_signals = signals_df[signals_df["Signal"] == "BUY"] if not signals_df.empty else None
        
        if buy_signals is None or buy_signals.empty:
            message = f"{title}\n\n⏸️ *No BUY signals meet threshold today.*\n\n Market conditions are neutral/bearish.\n Stay patient for high-conviction setups (≥75% strength).\n\nℹ️ {status_msg}"
        else:
            message = f"{title}\n\n🎯 *Top {min(5, len(buy_signals))} BUY Signals:*\n\n"
            for _, row in buy_signals.head(5).iterrows():
                stability_emoji = "✅" if "Continuation" in row.get("Signal_Stability", "") else ""
                message += f"{stability_emoji} *{row['Ticker']}*\n   💰 Price: ₦{row['Price(₦)']:,.2f}\n    Strength: {row['Strength(%)']}%\n   🔄 Status: {row.get('Signal_Stability', 'N/A')}\n   🎯 TP: ₦{row['Take_Profit']:,.2f} (+30%)\n   🛑 SL: ₦{row['Stop_Loss']:,.2f} (-7%)\n\n"
            if len(buy_signals) > 5: message += f" and {len(buy_signals) - 5} more signals\n\n"
        
        if fx_risk["alert"]: message += f"\n⚠️ *FX ALERT:* {fx_risk['message']}\n"
        else: message += f"\n✅ *FX Status:* {fx_risk['message']}\n"
        message += "\n📊 *Dashboard:* https://ngx-trading-dashboard.streamlit.app"
        message += "\n\n⏰ *Sent at:* " + datetime.now(lagos_tz).strftime("%H:%M WAT")
        
        send_telegram_alert(message)
        log_signals_to_sheet(signals_df, datetime.now().strftime("%Y-%m-%d"))
        print(f"✅ Complete. Duration: {(datetime.now(lagos_tz) - start_time).total_seconds():.1f}s")
    except Exception as e:
        print(f"❌ CRITICAL: {e}")

if __name__ == "__main__":
    run_alerts()
