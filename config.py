# config.py - System Configuration
# No changes needed

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

ALERT_PROBABILITY_THRESHOLD = 0.55  # 55% minimum strength
DASHBOARD_REFRESH_MINUTES = 30      # Auto-refresh interval

INITIAL_CAPITAL_NGN = 10_000_000    # ₦10M starting capital
MAX_POSITION_SIZE = 0.05            # 5% max per stock
STOP_LOSS_PCT = 0.07                # 7% stop loss
TAKE_PROFIT_PCT = 0.15              # 15% take profit

FX_RISK_THRESHOLD_PCT = 0.03        # 3% weekly FX move triggers warning
