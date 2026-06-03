import os
import asyncio
from collector import fetch_mlb_games
from analyzer import analyze_games
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TOKEN)


async def send_game(game):

    # 🔥 MENSAJE CORTO OPTIMIZADO
    msg = (
        f"⚾ {game['away_team']} vs {game['home_team']}\n"
        f"🎯 {game['pick']}\n"
        f"📊 {game['confidence']}% | ⚾ {game['total']} | {game['handicap']}\n"
        f"🏷 {game['level']}"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():

    print("🚀 MibotMLB V6 START")

    games = fetch_mlb_games()
    report = analyze_games(games)

    print(f"📊 VALUE PICKS: {len(report)}")

    # enviar uno por uno (estable)
    for g in report:
        await send_game(g)
        await asyncio.sleep(1)

    # TOP 5 limpio
    top = sorted(report, key=lambda x: x["confidence"], reverse=True)[:5]

    top_msg = "🔥 TOP 5\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}. {g['pick']} ({g['confidence']}%)\n"

    await bot.send_message(chat_id=CHAT_ID, text=top_msg)

    print("✅ V6 COMPLETO")


if __name__ == "__main__":
    asyncio.run(main())
