import os
import requests
from analyzer import run_analyzer

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode":"Markdown"}
    requests.post(url, data=payload)

def format_game(game):
    msg = f"⚾ {game['home_team']} vs {game['away_team']}\n\n"
    msg += f"🧾 Lanzadores\n"
    msg += f"{game['home_team']}: {game['home_pitcher']['name']} (ERA: {game['home_pitcher']['ERA']}, WHIP: {game['home_pitcher']['WHIP']})\n"
    msg += f"{game['away_team']}: {game['away_pitcher']['name']} (ERA: {game['away_pitcher']['ERA']}, WHIP: {game['away_pitcher']['WHIP']})\n\n"
    msg += f"🎯 Ganador sugerido: {game['pick']}\n"
    msg += f"⚾ Total carreras: {game['totals']}\n"
    msg += f"⚾ Hándicap: {game['handicap']}\n"
    msg += f"📊 Confianza: {game['confidence']}%\n"
    msg += f"🏷 Nivel: {game['level']}\n"
    msg += f"💎 Jugada recomendada: {game['pick']}\n"
    return msg

def main():
    games = run_analyzer()
    for g in games:
        message = format_game(g)
        send_telegram(message)
        print(message + "\n" + "━━━━━━━━━━━━━━\n")

if __name__=="__main__":
    main()
