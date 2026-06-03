import os
import requests
from analyzer import analyze_games
from datetime import datetime

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# FUNCIONES
# =========================
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error al enviar Telegram: {e}")

def fetch_games():
    try:
        resp = requests.get(URL, params={"apiKey": ODDS_API_KEY})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error al obtener juegos: {e}")
        return []

def format_game_message(game):
    home = game['home_team']
    away = game['away_team']
    hp = game['home_pitcher']
    ap = game['away_pitcher']

    winner = game['winner']
    winner_pct = game['winner_pct']
    total = game['total']
    total_type = game['total_type']
    total_pct = game['total_pct']
    handicap = game['handicap']
    handicap_team = game['handicap_team']
    handicap_pct = game['handicap_pct']
    confidence = game['confidence']
    level = game['level']
    recommendation = game['recommendation']

    msg = f"⚾ *{home} vs {away}*\n\n"
    msg += f"🧾 *Lanzadores*\n"
    msg += f"{home}: {hp['name']} (ERA {hp['era']} | WHIP {hp['whip']})\n"
    msg += f"{away}: {ap['name']} (ERA {ap['era']} | WHIP {ap['whip']})\n\n"

    msg += f"🎯 *Ganador:* {winner} ({winner_pct}%)\n"
    msg += f"⚾ *Total:* {total_type} {total} {total_pct}%\n"
    msg += f"⚾ *Hándicap:* {handicap} {handicap_team} {handicap_pct}%\n\n"

    msg += f"📊 *Confianza:* {confidence}%\n"
    msg += f"🏷 *Nivel:* {level}\n"
    msg += f"💎 *Jugada recomendada:* {recommendation}\n"

    return msg

def main():
    games = fetch_games()
    if not games:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return

    analyzed = analyze_games(games)

    # Enviar juegos en bloques de 3
    block = []
    for idx, game in enumerate(analyzed, 1):
        block.append(format_game_message(game))
        if idx % 3 == 0 or idx == len(analyzed):
            send_telegram_message("\n\n".join(block))
            block = []

    # Top Picks separados
    top_winners = [f"{g['home_team']} vs {g['away_team']} → {g['winner']} ({g['winner_pct']}%)" 
                   for g in analyzed if g['confidence'] >= 60 and g['recommendation'] != "NO JUGAR"]
    top_totals = [f"{g['home_team']} vs {g['away_team']} → {g['total_type']} {g['total']} ({g['total_pct']}%)"
                  for g in analyzed if g['confidence'] >= 60 and g['recommendation'] != "NO JUGAR"]
    top_handicaps = [f"{g['home_team']} vs {g['away_team']} → {g['handicap']} {g['handicap_team']} ({g['handicap_pct']}%)"
                     for g in analyzed if g['confidence'] >= 60 and g['recommendation'] != "NO JUGAR"]

    if top_winners:
        send_telegram_message("*🔥 TOP PICKS GANADOR*\n" + "\n".join(top_winners))
    if top_totals:
        send_telegram_message("*🔥 TOP PICKS TOTAL*\n" + "\n".join(top_totals))
    if top_handicaps:
        send_telegram_message("*🔥 TOP PICKS HÁNDICAP*\n" + "\n".join(top_handicaps))

if __name__ == "__main__":
    main()
