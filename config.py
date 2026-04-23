# config.py
# ⚙️ SETTINGS - Edit these later if needed

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

ALERT_PROBABILITY_THRESHOLD = 0.55  # 55% minimum strength to trigger alert
DASHBOARD_REFRESH_MINUTES = 30      # Auto-refresh interval
INITIAL_CAPITAL_NGN = 10_000_000    # ₦10M
MAX_POSITION_SIZE = 0.05            # 5% per stock
STOP_LOSS_PCT = 0.07                # 7%
TAKE_PROFIT_PCT = 0.15              # 15%
FX_RISK_THRESHOLD_PCT = 0.03        # 3% weekly FX move triggers warning
