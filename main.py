import os
import asyncio
from collector import fetch_mlb_games
from analyzer import analyze_games
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)


async def send_game(game):

    message = f"""⚾ {game['away_team']} vs {game['home_team']}

🧾 Lanzadores
{game['away_team']}: {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']})
{game['home_team']}: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']})

🎯 Ganador: {game['pick']}
⚾ Total: {game['total']}
⚾ Hándicap: {game['handicap']}

📊 Confianza: {game['confidence']}%
🏷 Nivel: {game['level']}

💎 Jugada recomendada:
{game['recommended']}
"""

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


async def main():

    print("🚀 MibotMLB V5.19 START")

    games = fetch_mlb_games()
    print(f"📊 Games loaded: {len(games)}")

    report = analyze_games(games)

    # enviar todos
    tasks = [send_game(g) for g in report]
    await asyncio.gather(*tasks)

    # TOP 5
    top = sorted(report, key=lambda x: x["confidence"], reverse=True)[:5]

    top_msg = "🔥 TOP 5 DEL DÍA\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}️⃣ {g['pick']} ({g['confidence']}%)\n"

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_msg)

    print("✅ Enviado todo correctamente")


if __name__ == "__main__":
    asyncio.run(main())
