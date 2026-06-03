import os
import asyncio
from collector import fetch_mlb_games
from analyzer import analyze_games
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)


# 🔥 mensaje compacto por bloque
async def send_block(block):

    msg = ""

    for g in block:

        # 🔥 indicador de valor
        tag = "🔥" if g.get("level") in ["🔥 ELITE", "✅ FUERTE"] else "⚪"

        msg += (
            f"{tag} {g['away_team']} vs {g['home_team']}\n"
            f"🎯 {g['pick']} | {g['confidence']}%\n"
            f"⚾ {g['total']} | {g['handicap']} | {g['level']}\n\n"
        )

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)


async def main():

    print("🚀 MibotMLB V7.2 PRO START")

    games = fetch_mlb_games()
    report = analyze_games(games, games)

    print(f"📊 TOTAL GAMES: {len(report)}")

    # 🔥 bloques más pequeños (MEJOR LEGIBILIDAD)
    block_size = 4

    for i in range(0, len(report), block_size):
        await send_block(report[i:i + block_size])
        await asyncio.sleep(1)

    # =========================
    # 🔥 TOP PICKS FINAL
    # =========================
    top = sorted(
        [g for g in report if g["level"] in ["🔥 ELITE", "✅ FUERTE"]],
        key=lambda x: x["confidence"],
        reverse=True
    )[:5]

    top_msg = "🔥 TOP PICKS DEL DÍA\n\n"

    for i, g in enumerate(top, 1):
        top_msg += (
            f"{i}. {g['pick']} ({g['confidence']}%)\n"
            f"   ⚾ {g['total']} | {g['handicap']}\n\n"
        )

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_msg)

    print("✅ V7.2 PRO COMPLETO")


if __name__ == "__main__":
    asyncio.run(main())
