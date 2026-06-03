import os
import asyncio
import requests
from analyzer import analyze_games
from telegram import Bot

# Configuración de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

def fetch_mlb_schedule():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=15)
        return res.json()
    except:
        return {}

async def send_game_message(game):
    header = f"⚾ {game['away_team']} vs {game['home_team']}"
    pitchers = (
        f"🧾 Lanzadores\n"
        f"{game['away_team']}: {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']})\n"
        f"{game['home_team']}: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']})"
    )
    outcome = (
        f"🎯 Ganador: {game['pick']}\n"
        f"⚾ Total: {game['total']}\n"
        f"⚾ Hándicap: {game['handicap']}"
    )
    confidence = f"📊 Confianza: {game['confidence']}%\n🏷 Nivel: {game['level']}\n💎 Jugada recomendada: {game['recommended']}"
    
    message = f"{header}\n\n{pitchers}\n\n{outcome}\n\n{confidence}"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def main():
    print("🚀 MibotMLB V7.3 PRO START")
    schedule = fetch_mlb_schedule()
    games_report = analyze_games(schedule)
    print(f"📊 Juegos procesados: {len(games_report)}")

    # Enviar en bloques de 3 juegos para no saturar
    batch_size = 3
    for i in range(0, len(games_report), batch_size):
        batch = games_report[i:i+batch_size]
        tasks = [send_game_message(game) for game in batch]
        await asyncio.gather(*tasks)

    # Mensaje final: TOP picks
    top_games = sorted(games_report, key=lambda x: x['confidence'], reverse=True)[:5]
    top_message = "🔥 TOP PICKS DEL DÍA\n\n"
    for i, g in enumerate(top_games, start=1):
        top_message += f"{i}. {g['pick']} ({g['confidence']}%) | {g['total']} | {g['handicap']} | {g['level']}\n"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_message)
    print("✅ Mensajes enviados!")

if __name__ == "__main__":
    asyncio.run(main())
