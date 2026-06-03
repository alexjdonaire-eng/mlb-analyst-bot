import os
import requests
from analyzer import analyze_games, fetch_mlb_games
from tracker import save_pick, daily_report

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def format_game(game):
    home = game.get("home_team")
    away = game.get("away_team")
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
f"{away}: {away_pitcher['name']} (ERA {away_pitcher['ERA']} | WHIP {away_pitcher['WHIP']})\n"
f"{home}: {home_pitcher['name']} (ERA {home_pitcher['ERA']} | WHIP {home_pitcher['WHIP']})\n\n"
f"🎯 Ganador: {winner.get('team', 'TBD')} ({winner.get('prob', 0)}%)\n"
f"⚾ Total: {total.get('type','ALTA')} {total.get('line','-')} ({total.get('prob',0)}%)\n"
f"⚾ Hándicap: {handicap.get('line','-')} ({handicap.get('prob',0)}%)\n\n"
f"📊 Confianza: {game.get('confidence',0)}%\n"
f"🏷 Nivel: {game.get('level','🚫 PASAR')}\n"
f"💎 Jugada: {pick_type} → {pick_value} ({game.get('confidence',0)}%)"
    )

def main():
    print("📡 MIBOTMLB START")
    games = fetch_mlb_games()
    if not games:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return

    # Analizar juegos con Odds API
    analyzed_games, top_message = analyze_games(games)

    # Enviar cada juego a Telegram
    for g in analyzed_games:
        msg = format_game(g)
        send_telegram_message(msg)

    # Guardar el TOP 5 en el tracker
    top5 = sorted(
        analyzed_games,
        key=lambda x: x["confidence"],
        reverse=True
    )[:5]

    for pick in top5:
        save_pick(
    pick["top_pick_game"],
    pick["top_pick_type"],
    pick["top_pick_value"]
)

    # Enviar TOP 5 a Telegram
    send_telegram_message(top_message)

    # Enviar resumen diario (opcional, si se ejecuta al final del día)
    # send_telegram_message(daily_report())

if __name__ == "__main__":
    main()
