import os
import asyncio
from analyzer import analyze_games
from collector import fetch_mlb_games
from telegram import Bot

# Configuración de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# Función para enviar mensajes en bloques
async def send_game_block(games_block):
    message = ""
    for game in games_block:
        line = (
            f"⚾ {game['away_team']} vs {game['home_team']}\n"
            f"🎯 Pick: {game['pick']}\n"
            f"📊 Confianza: {game['confidence']}% | ⚾ {game['total']} | {game['handicap']}\n"
            f"🏷 Nivel: {game['level']}\n"
        )
        # Resaltar los jugables
        if game['recommended'] != "NO JUGAR":
            line = f"🔥 {line}"
        message += line + "\n"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def main():
    print("🚀 MibotMLB V7.1 PRO START")
    
    # Descargar juegos
    print("📡 Descargando juegos MLB...")
    games_data = fetch_mlb_games()
    print(f"📊 Juegos descargados: {len(games_data)}")

    # Correr analyzer
    print("🧠 Corriendo analyzer...")
    games_report = analyze_games(games_data, games_data)

    # Enviar todos los juegos en bloques de 5
    block_size = 5
    for i in range(0, len(games_report), block_size):
        block = games_report[i:i + block_size]
        await send_game_block(block)

    # Enviar TOP PICKS
    top_games = sorted(
        [g for g in games_report if g['recommended'] != "NO JUGAR"],
        key=lambda x: x['confidence'],
        reverse=True
    )[:5]
    
    if top_games:
        top_message = "🔥 TOP PICKS DEL DÍA\n\n"
        for i, g in enumerate(top_games, start=1):
            top_message += f"{i}. {g['pick']} ({g['confidence']}%)\n"
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_message)

    print("✅ Mensajes enviados!")

if __name__ == "__main__":
    asyncio.run(main())
