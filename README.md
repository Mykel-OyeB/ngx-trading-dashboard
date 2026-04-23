# 🇬 NGX Algorithmic Trading Dashboard & Alert System

Automated daily trading signals for the Nigerian Stock Exchange. Get buy/sell alerts via Telegram + view live charts on a mobile-friendly dashboard. **No daily coding required.**

## 🚀 Quick Setup (Takes 5 Minutes)

### Step 1: Get Your Telegram Bot Credentials
1. Open Telegram → Search `@BotFather` → Send `/newbot`
2. Follow prompts to name your bot → **Copy the API Token**
3. Search `@userinfobot` → Send any message → **Copy your Chat ID**

### Step 2: Configure GitHub Secrets
1. In your GitHub repo → Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:
   - Name: `TELEGRAM_BOT_TOKEN` | Value: paste your token
   - Name: `TELEGRAM_CHAT_ID` | Value: paste your chat ID

### Step 3: Deploy the Dashboard (Free)
1. Go to [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub
2. Click **New app** → Select this repository
3. Main file: `app.py` → Click **Deploy!**
4. Bookmark the URL → Add to phone home screen

### Step 4: Test the Automation
1. Go to **Actions** tab → Click **Daily NGX Alerts** → **Run workflow**
2. Check Telegram → You should receive your first signal alert!

## 📱 How to Use Daily
- **Morning (8:00 AM WAT):** Check Telegram for automated buy/sell alerts
- **Anytime:** Open your Streamlit dashboard on phone/computer
- **Trading:** Always use **LIMIT orders**, max 5% per position, set hard stops at -7%

## 📁 Project Files
| File | Purpose |
|------|---------|
| `app.py` | Live dashboard (what you view daily) |
| `alerts.py` | Telegram alert system (runs automatically) |
| `data_engine.py` | Signal generator & market data |
| `config.py` | Your settings & thresholds |
| `requirements.txt` | Python dependencies |
| `.github/workflows/` | Automation schedule (runs daily at 8 AM) |

## 🔄 How Automation Works
- GitHub Actions runs `alerts.py` every weekday at **8:00 AM WAT**
- No manual work needed. Alerts arrive in Telegram automatically.
- Dashboard auto-refreshes every 30 minutes.

## ⚠️ Important Notes
-  Never share your Telegram token or GitHub secrets
- 📊 This uses simulated data by default. Connect real NGX APIs in `data_engine.py` when ready
- 📉 NGX trading carries liquidity, FX, and regulatory risks. Paper trade first.
- 💡 Add to phone home screen: Safari/Chrome → Share → "Add to Home Screen"

## 🤝 Need Help?
- Check GitHub Issues tab
- Re-read this guide step-by-step
- Ensure secrets are correctly named & added
- Verify Telegram bot is not blocked

**Happy Trading! 🇬📈**
