import os
import asyncio
from telegram import Bot
from analyzer import analyze_games
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_game(game):
    """Envía un juego formateado a Telegram"""
    msg = f"⚾ {game['away_team']} vs {game['home_team']}\n\n"
    msg += "🧾 Lanzadores\n"
    msg += f"{game['away_team']}: {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']})\n"
    msg += f"{game['home_team']}: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']})\n\n"
    msg += f"🎯 Ganador: {game['pick']} ({game['confidence']}%)\n"
    msg += f"⚾ Total: {game['total_label']} {game['total']} {game['total_percent']}%\n"
    msg += f"⚾ Hándicap: {game['handicap']} {game['pick']} {game['handicap_percent']}%\n\n"
    msg += f"📊 Confianza: {game['confidence']}%\n"
    msg += f"🏷 Nivel: {game['level']}\n"
    msg += f"💎 Jugada recomendada: {game['recommended']}\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def main():
    # Ejemplo: Obtener schedule desde MLB API
    res = requests.get("https://statsapi.mlb.com/api/v1/schedule?sportId=1")
    schedule = res.json()
    report, top_picks = analyze_games(schedule)

    # Enviar todos los juegos
    for game in report:
        await send_game(game)
        await asyncio.sleep(0.5)  # Pequeña pausa para no saturar

    # Enviar Top Picks
    top_msg = "🔥 TOP PICKS DEL DÍA\n\n"
    for i, game in enumerate(top_picks,1):
        top_msg += f"{i}. {game['pick']} gana ({game['confidence']}%)\n"
    await bot.send_message(chat_id=CHAT_ID, text=top_msg)

if __name__ == "__main__":
    asyncio.run(main())
