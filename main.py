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

    print("🚀 V6 CLEAN START")

    games = fetch_mlb_games()
    picks = analyze_games(games)

    print(f"📊 VALUE PICKS: {len(picks)}")

    # 🔥 SOLO JUEGOS IMPORTANTES
    for g in picks:
        await send_game(g)
        await asyncio.sleep(1)

    # 🔥 SOLO 1 TOP FINAL (NO DUPLICAR MÁS)
    top = picks[:5]

    top_msg = "🔥 TOP 5\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}. {g['pick']} ({g['confidence']}%)\n"

    await bot.send_message(CHAT_ID, top_msg)

    print("✅ DONE CLEAN OUTPUT")


if __name__ == "__main__":
    asyncio.run(main())
