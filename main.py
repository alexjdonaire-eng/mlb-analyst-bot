import os
import asyncio
from analyzer import analyze_games
from collector import fetch_mlb_games
from telegram import Bot

# Configuración de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_game_message(game):
    message = f"""⚾ {game['away_team']} vs {game['home_team']}

🧾 Lanzadores
{game['away_team']}: {game['away_pitcher']['name']} (ERA: {game['away_pitcher']['ERA']}, WHIP: {game['away_pitcher']['WHIP']})
{game['home_team']}: {game['home_pitcher']['name']} (ERA: {game['home_pitcher']['ERA']}, WHIP: {game['home_pitcher']['WHIP']})

🎯 Ganador sugerido: {game['pick']}
⚾ Total carreras: {game['total']}
⚾ Hándicap: {game['handicap']}
📊 Confianza: {game['confidence']}%
🏷 Nivel: {game['level']}
💎 Jugada recomendada: {game['recommended']}
"""
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def main():
    print("🚀 MibotMLB V5.18 START")
    print("📡 Descargando juegos MLB...")
    games_data = fetch_mlb_games()
    print(f"📊 Juegos descargados: {len(games_data)}")

    print("🧠 Corriendo analyzer...")
    games_report = analyze_games(games_data, games_data)  # Usamos los datos del collector directamente

    tasks = [send_game_message(game) for game in games_report]
    await asyncio.gather(*tasks)

    # Opcional: enviar TOP 5 del día
    top_games = sorted(games_report, key=lambda x: x['confidence'], reverse=True)[:5]
    top_message = "🔥 TOP 5 DEL DÍA\n\n"
    for i, g in enumerate(top_games, start=1):
        top_message += f"{i}️⃣ {g['pick']} — {g['confidence']}%\n"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_message)
    print("✅ Mensajes enviados!")

if __name__ == "__main__":
    asyncio.run(main())
