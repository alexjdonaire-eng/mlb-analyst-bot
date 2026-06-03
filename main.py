import os
import asyncio
from telegram import Bot
from collector import fetch_mlb_games
from analyzer import analyze_games

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
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"✅ Sent: {game['away_team']} vs {game['home_team']}")
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

async def main():
    print("🚀 MibotMLB V5.18 START")
    
    # Descargar juegos
    print("📡 Descargando juegos MLB...")
    games_data = fetch_mlb_games()
    print(f"📊 Juegos descargados: {len(games_data)}")
    
    # Analizar juegos
    print("🧠 Corriendo analyzer...")
    games_report = analyze_games({"dates":[{"games": games_data}]}, games_data)  # formato compatible con analyzer

    # Enviar mensajes individuales
    tasks = [send_game_message(game) for game in games_report]
    await asyncio.gather(*tasks)

    # Enviar TOP 5 por confianza
    top5 = sorted(games_report, key=lambda x: x["confidence"], reverse=True)[:5]
    top_msg = "🔥 TOP 5 DEL DÍA\n\n"
    for i, g in enumerate(top5, 1):
        top_msg += f"{i}️⃣ {g['pick']} — {g['confidence']}%\n"

    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_msg)
        print("✅ TOP 5 enviado")
    except Exception as e:
        print(f"❌ Error enviando TOP 5: {e}")

if __name__ == "__main__":
    asyncio.run(main())
