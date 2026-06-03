import os
import requests
from analyzer import run_analyzer
import time

# =========================
# TELEGRAM CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM CONFIG MISSING")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# =========================
# RUN ANALYZER & SEND
# =========================
if __name__ == "__main__":
    games = run_analyzer()
    for g in games:
        msg = f"""⚾ {g['home_team']} vs {g['away_team']}

🎯 Pick: {g['pick']}
📊 Confianza: {g['confidence']}%
📈 Edge: {g['edge']}%
📡 Steam: {g['steam']}
📉 Market Move: {g['market_move']}
🧾 Pitchers: {g['home_pitcher']['name']} (ERA {g['home_pitcher']['ERA']}, WHIP {g['home_pitcher']['WHIP']}) vs {g['away_pitcher']['name']} (ERA {g['away_pitcher']['ERA']}, WHIP {g['away_pitcher']['WHIP']})
🧠 Score: {g['score']}
🏷 Nivel: {g['level']}
━━━━━━━━━━━━━━"""
        send_telegram(msg)
        time.sleep(1)  # para no saturar Telegram
