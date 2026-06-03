import os
import requests
import asyncio
import traceback
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
    except Exception as e:
        print(f"❌ Fetch error: {e}")
        return {}

def fetch_mlb_schedule():
    return fetch_json(MLB_SCHEDULE_URL)

def fetch_odds():
    return fetch_json(ODDS_API_URL)

async def send_game_message(game):

    try:
        message = f"""⚾ {game['away_team']} vs {game['home_team']}

🧾 Lanzadores

{game['away_team']}
• {game['away_pitcher']['name']}
• ERA: {game['away_pitcher']['ERA']}
• WHIP: {game['away_pitcher']['WHIP']}

{game['home_team']}
• {game['home_pitcher']['name']}
• ERA: {game['home_pitcher']['ERA']}
• WHIP: {game['home_pitcher']['WHIP']}

🎯 Ganador sugerido:
{game['pick']}

⚾ Total carreras:
{game['total']}

⚾ Hándicap:
{game['handicap']}

📊 Confianza:
{game['confidence']}%

🏷 Nivel:
{game['level']}

💎 Jugada recomendada:
{game['recommended']}
"""

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )

        print(f"✅ Sent: {game['away_team']} vs {game['home_team']}")

    except Exception as e:
        print(f"❌ Telegram error: {e}")
        traceback.print_exc()

async def main():

    print("🚀 MibotMLB V5.16 START")

    try:

        print("📡 Downloading MLB schedule...")
        schedule = fetch_mlb_schedule()

        print("📡 Downloading Odds...")
        odds = fetch_odds()

        print("🧠 Running analyzer...")
        games_report = analyze_games(schedule, odds)

        if not games_report:
            print("❌ Analyzer returned 0 games")
            return

        print(f"📊 Games returned: {len(games_report)}")

        for game in games_report:
            await send_game_message(game)

        print("✅ Finished")

    except Exception as e:
        print(f"❌ MAIN ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
