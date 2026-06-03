import os
import asyncio
import requests
from analyzer import analyze_games
from telegram import Bot

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

def format_game(game):
    # Determinar total Alta/Baja (simulado)
    total_label = "Alta" if game['pick'] == game['away_team'] else "Baja"
    total_pct = f"{game['confidence'] + 20:.1f}%" if game['confidence'] >= 50 else f"{game['confidence']:.1f}%"

    header = f"⚾ {game['away_team']} vs {game['home_team']}\n"
    pitchers = (
        f"\n🧾 Lanzadores\n"
        f"{game['away_team']}: {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']})\n"
        f"{game['home_team']}: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']})\n"
    )
    outcome = (
        f"\n🎯 Ganador: {game['pick']} ({game['confidence']}%)\n"
        f"⚾ Total: {total_label} {game['total']} {total_pct}\n"
        f"⚾ Hándicap: {game['handicap']} {game['pick']} {game['confidence']}%\n"
    )
    confidence = f"\n📊 Confianza: {game['confidence']}%\n🏷 Nivel: {game['level']}\n"
    recommended = f"💎 Jugada recomendada: {game['recommended']}"
    
    return f"{header}{pitchers}{outcome}{confidence}{recommended}"

async def send_game_message(game):
    message = format_game(game)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

async def main():
    print("🚀 MibotMLB V7.5 PRO START")
    schedule = fetch_mlb_schedule()
    games_report = analyze_games(schedule)
    print(f"📊 Juegos procesados: {len(games_report)}")

    # Enviar en bloques de 3 juegos
    batch_size = 3
    for i in range(0, len(games_report), batch_size):
        batch = games_report[i:i+batch_size]
        tasks = [send_game_message(game) for game in batch]
        await asyncio.gather(*tasks)

    # TOP PICKS resumido
    top_games = sorted(games_report, key=lambda x: x['confidence'], reverse=True)[:5]
    top_message = "🔥 *TOP PICKS DEL DÍA*\n\n"
    for g in top_games:
        # Elegir resumen: gana / hándicap / alta/baja
        total_label = "Alta" if g['pick'] == g['away_team'] else "Baja"
        top_message += f"{g['pick']} gana | {g['handicap']} | {total_label} {g['total']}\n"
    
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=top_message, parse_mode="Markdown")
    print("✅ Mensajes enviados!")

if __name__ == "__main__":
    asyncio.run(main())
