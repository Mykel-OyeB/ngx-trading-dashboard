# alerts.py - TELEGRAM + GOOGLE SHEETS LOGGING
# ✅ FIXED: JSON sanitization to prevent NaN/Inf serialization errors

import requests
import os
import numpy as np
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
        data = signal_tab.get_all_values()
        if len(data) < 2: return {}
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        dates = [str(row[0]).strip() for row in data[1:] if row and row[0]]
        prev_dates = [d for d in dates if d != today_str]
        if not prev_dates: return {}
        latest_prev = max(prev_dates)
        
        prev_signals = {}
        for row in data[1:]:
            if row and str(row[0]).strip() == latest_prev and len(row) >= 3:
                prev_signals[row[1].strip()] = row[2].strip()
        return prev_signals
    except Exception as e:
        print(f"⚠️ get_previous_signals failed: {e}")
        return {}

def log_signals_to_sheet(signals_df, date_str):
    """Hardened sheet logging with JSON sanitization + explicit error trapping"""
    try:
        print(f"📝 [LOG] Starting sheet append for date: {date_str}")
        print(f" [LOG] DataFrame rows to append: {len(signals_df)}")
        
        # ✅ JSON SANITIZATION: Replace NaN/Inf with 0 for numeric columns only
        numeric_cols = signals_df.select_dtypes(include=['number']).columns
        signals_df[numeric_cols] = signals_df[numeric_cols].replace([np.inf, -np.inf], 0).fillna(0)
        print(f"✅ [LOG] Sanitized numeric columns for Sheets API compatibility")
        
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
        
        # ✅ DEDUPLICATION with validation
        all_values = signal_tab.get_all_values()
        rows_to_delete = []
        for i, row in enumerate(all_values):
            if row and str(row[0]).strip() == date_str:
                rows_to_delete.append(i + 1)
        
        if rows_to_delete:
            print(f"🗑️ [LOG] Deleting {len(rows_to_delete)} existing rows for {date_str}")
            for row_num in sorted(rows_to_delete, reverse=True):
                signal_tab.delete_rows(row_num)
            print(f"✅ [LOG] Deduplication complete")
        else:
            print(f"️ [LOG] No existing rows for {date_str} (first run today)")
        
        # ✅ PREPARE ROWS
        rows_to_add = []
        for _, row in signals_df.iterrows():
            rows_to_add.append([
                date_str, row['Ticker'], row['Signal'], row['Strength(%)'],
                row['Price(₦)'], row['Stop_Loss'], row['Take_Profit'], row['Reasons'],
                row['SMA20'], row['SMA50'], row['RSI'], row['MACD_Hist'],
                row['Liquidity_Flag'], row['Event_Tag'],
                row['Entry_Zone_Low'], row['Entry_Zone_High'],
                row['Chase_Warning'], row['Pullback_Watch'],
                row['Signal_Stability'], row.get('Drawdown_Alert', '✅ Within Range')
            ])
        
        if not rows_to_add:
            print(f"⚠️ [LOG] No rows to append. Exiting.")
            return False
            
        # ✅ APPEND
        print(f"📤 [LOG] Appending {len(rows_to_add)} rows to SignalHistory...")
        signal_tab.append_rows(rows_to_add, value_input_option='USER_ENTERED')
        print(f"✅ [LOG] Successfully logged {len(rows_to_add)} signals to Google Sheets")
        return True
        
    except gspread.exceptions.APIError as api_err:
        print(f" [LOG] Google Sheets API Error: {api_err}")
        return False
    except Exception as e:
        print(f"❌ [LOG] Unexpected sheet error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_alerts():
    lagos_tz = pytz.timezone('Africa/Lagos')
    start_time = datetime.now(lagos_tz)
    print(f"🚀 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')} WAT")
    try:
        prev_signals = get_previous_signals()
        signals_df, status_msg = generate_ngx_signals(prev_signals)
        print(f" Generated {len(signals_df)} signals")
        
        fx_risk = get_fx_risk_alert()
        today = datetime.now().strftime("%B %d, %Y")
        title = f"🇬 *NGX SIGNALS - {today}*"
        buy_signals = signals_df[signals_df["Signal"] == "BUY"] if not signals_df.empty else None
        
        if buy_signals is None or buy_signals.empty:
            message = f"{title}\n\n⏸️ *No BUY signals meet threshold today.*\n\n Market conditions are neutral/bearish.\n Stay patient for high-conviction setups (≥75% strength).\n\nℹ️ {status_msg}"
        else:
            message = f"{title}\n\n🎯 *Top {min(5, len(buy_signals))} BUY Signals:*\n\n"
            for _, row in buy_signals.head(5).iterrows():
                stability_emoji = "✅" if "Continuation" in row.get("Signal_Stability", "") else ""
                message += f"{stability_emoji} *{row['Ticker']}*\n   💰 Price: ₦{row['Price(₦)']:,.2f}\n    Strength: {row['Strength(%)']}%\n    Status: {row.get('Signal_Stability', 'N/A')}\n   🎯 TP: {row['Take_Profit']:,.2f} (+30%)\n   🛑 SL: ₦{row['Stop_Loss']:,.2f} (-7%)\n\n"
            if len(buy_signals) > 5: message += f" and {len(buy_signals) - 5} more signals\n\n"
        
        if fx_risk["alert"]: message += f"\n⚠️ *FX ALERT:* {fx_risk['message']}\n"
        else: message += f"\n✅ *FX Status:* {fx_risk['message']}\n"
        message += "\n📊 *Dashboard:* https://ngx-trading-dashboard.streamlit.app"
        message += "\n\n⏰ *Sent at:* " + datetime.now(lagos_tz).strftime("%H:%M WAT")
        
        send_telegram_alert(message)
        
        # ✅ HARDED LOGGING CALL
        log_success = log_signals_to_sheet(signals_df, datetime.now().strftime("%Y-%m-%d"))
        if not log_success:
            print("⚠️ [ALERT] Sheet logging failed. Check API permissions or rate limits.")
            
        print(f"✅ Complete. Duration: {(datetime.now(lagos_tz) - start_time).total_seconds():.1f}s")
    except Exception as e:
        print(f"❌ CRITICAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_alerts()
