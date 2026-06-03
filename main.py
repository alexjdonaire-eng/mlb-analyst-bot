import os
import asyncio
import requests
from analyzer import analyze_games
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

MLB_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"


def fetch_mlb():
    try:
        r = requests.get(MLB_URL, timeout=20)
        return r.json()
    except:
        return {}


def build_message(game):
    return f"""⚾ {game['away_team']} vs {game['home_team']}

🧾 Lanzadores
{game['away_team']}: {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']})
{game['home_team']}: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']})

🎯 Ganador: {game['pick']} ({game['confidence']}%)

⚾ Total: {game['total']}
⚾ Hándicap: {game['handicap']}

📊 Confianza: {game['confidence']}%
🏷 Nivel: {game['level']}
💎 Jugada: {game['recommended']}
"""


async def send_safe(text):
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text
        )
    except Exception as e:
        print("Telegram error:", e)


async def main():
    print("🚀 MibotMLB V7.8 START")

    schedule = fetch_mlb()

    games = analyze_games(schedule)

    print(f"📊 Games loaded: {len(games)}")

    # 🔥 enviar en bloques pequeños (evita timeout)
    for game in games:
        msg = build_message(game)
        await send_safe(msg)
        await asyncio.sleep(0.5)

    # TOP PICKS
    top = sorted(games, key=lambda x: x["confidence"], reverse=True)[:5]

    top_msg = "🔥 TOP PICKS DEL DÍA\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}. {g['away_team']} vs {g['home_team']} → {g['pick']} ({g['confidence']}%)\n"

    await send_safe(top_msg)

    print("✅ DONE")


if __name__ == "__main__":
    asyncio.run(main())
