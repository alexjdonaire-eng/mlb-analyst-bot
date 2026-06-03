import os
import asyncio
import requests
from telegram import Bot
from analyzer import analyze_games

# =========================
# CONFIG
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

MLB_SCHEDULE_URL = (
    "https://statsapi.mlb.com/api/v1/schedule"
    "?sportId=1&hydrate=probablePitcher,team"
)

ODDS_API_URL = (
    f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/"
    f"?apiKey={ODDS_API_KEY}"
    "&regions=us"
    "&markets=h2h,spreads,totals"
)

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# HELPERS
# =========================

def fetch_json(url, timeout=20):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Error descargando datos: {e}")
        return {}

def fetch_schedule():
    print("📡 Descargando calendario MLB...")
    return fetch_json(MLB_SCHEDULE_URL)

def fetch_odds():
    print("📡 Descargando cuotas...")
    return fetch_json(ODDS_API_URL)

# =========================
# TELEGRAM
# =========================

async def send_game(game):

    mensaje = f"""⚾ {game['away_team']} vs {game['home_team']}

🧾 Lanzadores

{game['away_team']}
• {game['away_pitcher']['name']}
• ERA: {game['away_pitcher']['ERA']}
• WHIP: {game['away_pitcher']['WHIP']}

{game['home_team']}
• {game['home_pitcher']['name']}
• ERA: {game['home_pitcher']['ERA']}
• WHIP: {game['home_pitcher']['WHIP']}

🎯 Ganador sugerido:
{game['pick']}

⚾ Total de carreras:
{game['total']}

⚾ Hándicap:
{game['handicap']}

📊 Confianza:
{game['confidence']}%

🏷 Nivel:
{game['level']}

💎 Jugada recomendada:
{game['recommended']}
"""

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=mensaje
    )

# =========================
# MAIN
# =========================

async def main():

    print("🚀 MibotMLB V5.17 START")

    schedule = fetch_schedule()
    odds = fetch_odds()

    games = analyze_games(schedule, odds)

    print(f"📊 Juegos analizados: {len(games)}")

    if not games:
        print("❌ No hay juegos para enviar")
        return

    enviados = 0

    for game in games:
        try:
            await send_game(game)
            enviados += 1
            print(
                f"✅ Enviado: "
                f"{game['away_team']} vs {game['home_team']}"
            )

        except Exception as e:
            print(
                f"❌ Error enviando "
                f"{game['away_team']} vs {game['home_team']}: {e}"
            )

    print(f"🏁 Finalizado. Mensajes enviados: {enviados}")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    asyncio.run(main())
