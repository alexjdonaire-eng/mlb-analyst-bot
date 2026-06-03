import os
import requests
from analyzer import analyze_games

API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_games():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(API_URL, headers=headers)
    if response.status_code != 200:
        return []
    return response.json()

def format_game(game):
    home = game.get("home_team")
    away = game.get("away_team")
    home_pitcher = game.get("home_pitcher", {"name": "TBD", "era": "-", "whip": "-"})
    away_pitcher = game.get("away_pitcher", {"name": "TBD", "era": "-", "whip": "-"})
    
    winner = game.get("predicted_winner", {})
    total = game.get("predicted_total", {})
    handicap = game.get("predicted_handicap", {})
    
    # Determinar jugada
    pick_type = game.get("top_pick_type", "Ganador")
    pick_value = game.get("top_pick_value", winner.get("team", ""))
    
    return (
f"⚾ {away} vs {home}\n\n"
f"🧾 Lanzadores\n"
f"{away}: {away_pitcher['name']} (ERA {away_pitcher['era']} | WHIP {away_pitcher['whip']})\n"
f"{home}: {home_pitcher['name']} (ERA {home_pitcher['era']} | WHIP {home_pitcher['whip']})\n\n"
f"🎯 Ganador: {winner.get('team', 'TBD')} ({winner.get('prob', 0)}%)\n"
f"⚾ Total: {total.get('line', '-')} ({total.get('prob', 0)}%)\n"
f"⚾ Hándicap: {handicap.get('line', '-')} ({handicap.get('prob', 0)}%)\n\n"
f"📊 Confianza: {game.get('confidence', 0)}%\n"
f"🏷 Nivel: {game.get('level', '🚫 PASAR')}\n"
f"💎 Jugada: {pick_type} → {pick_value}"
    )

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    games = fetch_games()
    if not games:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return
    
    analyzed_games = analyze_games(games)
    
    # Formatear y enviar cada juego
    for g in analyzed_games:
        msg = format_game(g)
        send_telegram_message(msg)
    
    # Top 5 picks mezclados
    top5 = sorted(analyzed_games, key=lambda x: x.get("confidence", 0), reverse=True)[:5]
    top_msg = "🔥 TOP 5 PICKS DEL DÍA\n\n"
    for t in top5:
        top_msg += f"{t.get('top_pick_type', 'Ganador')} → {t.get('top_pick_value', '')} ({t.get('confidence', 0)}%)\n"
    send_telegram_message(top_msg)

if __name__ == "__main__":
    main()
