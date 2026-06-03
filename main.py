import os
import requests
from analyzer import analyze_games
from datetime import datetime

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
SPORT = "baseball_mlb"
API_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

# =========================
# FUNCTIONS
# =========================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    return response.json()

def fetch_games():
    params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "h2h,spreads,totals"}
    r = requests.get(API_URL, params=params)
    if r.status_code != 200:
        print("⚠️ Error al obtener datos:", r.text)
        return []
    data = r.json()
    if not data:
        print("⚠️ No hay juegos hoy o error al obtener datos.")
        return []
    return data

def format_game(g):
    return f"""
⚾ {g['home']} vs {g['away']}

🧾 Lanzadores
{g['home']}: {g['home_pitcher']['name']} (ERA {g['home_pitcher']['era']} | WHIP {g['home_pitcher']['whip']})
{g['away']}: {g['away_pitcher']['name']} (ERA {g['away_pitcher']['era']} | WHIP {g['away_pitcher']['whip']})

🎯 Ganador: {g['winner']} ({g['confidence']}%)

⚾ Total: {g['total_type']} {g['total']}
⚾ Hándicap: {g['spread_team']} -1.5

📊 Confianza: {g['confidence']}%
🏷 Nivel: {g['level']}
💎 Jugada: {g['recommendation']}

━━━━━━━━━━━━━━
"""

def main():
    print("🚀 Iniciando MLB Bot V9 PRO")
    games_raw = fetch_games()
    if not games_raw:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return

    # Analizar juegos
    games = analyze_games(games_raw)
    if not games:
        send_telegram_message("⚠️ No hay juegos jugables hoy.")
        return

    # Enviar cada juego en bloque separado
    for g in games:
        message = format_game(g)
        send_telegram_message(message)

    # Top Picks separados
    top_winners = [f"{g['winner']} gana ({g['confidence']}%)" for g in games if g['confidence'] >= 55]
    top_totals = [f"{g['total_type']} {g['total']} ({g['confidence']}%)" for g in games if g['confidence'] >= 55]
    top_spreads = [f"{g['spread_team']} -1.5 ({g['confidence']}%)" for g in games if g['confidence'] >= 55]

    if top_winners:
        send_telegram_message("🔥 <b>TOP PICKS - GANADOR</b>\n" + "\n".join(top_winners))
    if top_totals:
        send_telegram_message("🔥 <b>TOP PICKS - TOTAL</b>\n" + "\n".join(top_totals))
    if top_spreads:
        send_telegram_message("🔥 <b>TOP PICKS - HÁNDICAP</b>\n" + "\n".join(top_spreads))

if __name__ == "__main__":
    main()
