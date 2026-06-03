import os
from analyzer import run_analyzer
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def format_game(g):
    hp = g["home_pitcher"]
    ap = g["away_pitcher"]
    msg = f"""
⚾ {g['home_team']} vs {g['away_team']}

🎯 Pick: {g['pick']}
📊 Confianza: {g['confidence']}%
📈 Edge: {g['edge']}%
📡 Steam: {g['steam']}
📉 Market Move: {g['market_move']}
🧾 Pitchers: {hp['name']} (ERA {hp['ERA']}, WHIP {hp['WHIP']}) vs {ap['name']} (ERA {ap['ERA']}, WHIP {ap['WHIP']})
🧠 Score: {g['score']}
🏷 Nivel: {g['level']}
━━━━━━━━━━━━━━
"""
    return msg

def main():
    games = run_analyzer()
    for g in games:
        send_telegram(format_game(g))
    print("✅ Messages sent to Telegram")

if __name__ == "__main__":
    main()
