import os
import asyncio
from collector import fetch_mlb_games
from analyzer import analyze_games
from telegram import Bot

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


async def send_game(g):

    msg = (
        f"⚾ {g['away_team']} vs {g['home_team']}\n"
        f"🎯 {g['pick']}\n"
        f"📊 {g['confidence']}% | ⚾ {g['total']} | {g['handicap']}\n"
        f"🏷 {g['level']}"
    )

    await bot.send_message(CHAT_ID, msg)


async def main():

    print("🚀 V7 PRO SCANNER START")

    games = fetch_mlb_games()
    report = analyze_games(games)

    print(f"📊 TOTAL GAMES: {len(report)}")

    # TODOS LOS JUEGOS
    for g in report:
        await send_game(g)
        await asyncio.sleep(0.8)

    # TOP PICKS REAL (solo ranking, no elimina nada)
    top = report[:5]

    top_msg = "🔥 TOP PICKS DEL DÍA\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}. {g['pick']} ({g['confidence']}%)\n"

    await bot.send_message(chat_id=CHAT_ID, text=top_msg)

    print("✅ V7 PRO COMPLETO")


if __name__ == "__main__":
    asyncio.run(main())
