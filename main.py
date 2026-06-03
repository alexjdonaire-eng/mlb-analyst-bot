import os
from collector import run
from analyzer import analyze_games
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def format_game(game):
    home = game.get("home")
    away = game.get("away")
    home_pitcher = game.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
    away_pitcher = game.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})

    winner = game.get("predicted_winner", {})
    total = game.get("predicted_total", {})
    handicap = game.get("predicted_handicap", {})

    pick_type = game.get("top_pick_type", "Ganador")
    pick_value = game.get("top_pick_value", winner.get("team", ""))

    return (
f"⚾ {away} vs {home}\n\n"
f"🧾 Lanzadores\n"
f"{away}: {away_pitcher.get('name','TBD')} (ERA {away_pitcher.get('ERA','-')} | WHIP {away_pitcher.get('WHIP','-')})\n"
f"{home}: {home_pitcher.get('name','TBD')} (ERA {home_pitcher.get('ERA','-')} | WHIP {home_pitcher.get('WHIP','-')})\n\n"
f"🎯 Ganador: {winner.get('team','TBD')} ({winner.get('prob',0)}%)\n"
f"⚾ Total: {total.get('line','-')} ({total.get('prob',0)}%)\n"
f"⚾ Hándicap: {handicap.get('line','-')} ({handicap.get('prob',0)}%)\n\n"
f"📊 Confianza: {game.get('confidence',0)}%\n"
f"🏷 Nivel: {game.get('level','🚫 PASAR')}\n"
f"💎 Jugada: {pick_type} → {pick_value}"
    )

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    games = run()
    if not games:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return

    analyzed_games = analyze_games(games)

    for g in analyzed_games:
        msg = format_game(g)
        send_telegram_message(msg)

    # Top 5 picks mezclados
    top5 = sorted(analyzed_games, key=lambda x: x.get("confidence",0), reverse=True)[:5]
    top_msg = "🔥 TOP 5 PICKS DEL DÍA\n\n"
    for t in top5:
        top_msg += f"{t.get('top_pick_type','Ganador')} → {t.get('top_pick_value','')} ({t.get('confidence',0)}%)\n"
    send_telegram_message(top_msg)

if __name__ == "__main__":
    main()
