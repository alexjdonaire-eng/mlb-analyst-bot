import os
import requests
from analyzer import analyze_games
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals"

bot = Bot(token=TELEGRAM_TOKEN)

def fetch_json(url, timeout=15):
    try:
        res = requests.get(url, timeout=timeout)
        return res.json()
    except:
        return {}

def fetch_mlb_schedule():
    return fetch_json(MLB_SCHEDULE_URL)

def fetch_odds():
    return fetch_json(ODDS_API_URL)

def run():
    schedule = fetch_mlb_schedule()
    odds = fetch_odds()
    games_report = analyze_games(schedule, odds)

    for g in games_report:
        message = f"""⚾ {g['away_team']} vs {g['home_team']}

🧾 Lanzadores
{g['away_team']}: {g['away_pitcher']['name']} (ERA: {g['away_pitcher']['ERA']}, WHIP: {g['away_pitcher']['WHIP']})
{g['home_team']}: {g['home_pitcher']['name']} (ERA: {g['home_pitcher']['ERA']}, WHIP: {g['home_pitcher']['WHIP']})

🎯 Ganador sugerido: {g['pick']}
⚾ Total carreras: {g['total']}
⚾ Hándicap: {g['handicap']}
📊 Confianza: {g['confidence']}%
🏷 Nivel: {g['level']}
💎 Jugada recomendada: {g['recommended']}
"""
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

if __name__ == "__main__":
    print("🚀 MibotMLB V5.16 START")
    run()
