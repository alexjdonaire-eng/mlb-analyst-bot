import os
import requests
from analyzer import run as run_analyzer

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def send_telegram(msg):
    try:
        requests.post(TELEGRAM_URL, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

def format_game(game):
    hp = game["home_pitcher"]
    ap = game["away_pitcher"]
    msg = f"""
⚾ *{game['home_team']} vs {game['away_team']}*

🧾 *Lanzadores*
{game['home_team']}: {hp['name']} (ERA: {hp['ERA']}, WHIP: {hp['WHIP']})
{game['away_team']}: {ap['name']} (ERA: {ap['ERA']}, WHIP: {ap['WHIP']})

🎯 *Ganador sugerido:* {game['pick']}
⚾ *Total carreras:* {game['total']}
⚾ *Hándicap:* {game['spread']}
📊 *Confianza:* {game['confidence']}%
🏷 *Nivel:* {game['level']}
💎 *Jugada recomendada:* {game['pick']}
"""
    return msg

if __name__ == "__main__":
    print("📡 MAIN V5.16 START")
    games = run_analyzer()
    for g in games:
        msg = format_game(g)
        send_telegram(msg)
    print("✅ Mensajes enviados a Telegram")
