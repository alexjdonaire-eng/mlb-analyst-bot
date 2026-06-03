import os
import time
import requests
from analyzer import fetch_mlb_games, analyze_games
from tracker import save_pick, daily_report
from grader import grade_picks

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM
# =========================
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

# =========================
# FORMATO JUEGO
# =========================
def format_game(game):
    home = game["home_team"]
    away = game["away_team"]

    hp = game["home_pitcher"]
    ap = game["away_pitcher"]

    winner = game["predicted_winner"]
    total = game["predicted_total"]
    handicap = game["predicted_handicap"]

    return (
f"⚾ {away} vs {home}\n\n"
f"🧾 Lanzadores\n"
f"{away}: {ap['name']} (ERA {ap['ERA']} | WHIP {ap['WHIP']})\n"
f"{home}: {hp['name']} (ERA {hp['ERA']} | WHIP {hp['WHIP']})\n\n"
f"🎯 Ganador: {winner['team']} ({winner['prob']}%)\n"
f"⚾ Total: {total['type']} {total['line']} ({total['prob']}%)\n"
f"⚾ Hándicap: {handicap['line']} ({handicap['prob']}%)\n\n"
f"📊 Confianza: {game['confidence']}%\n"
f"🏷 Nivel: {game['level']}\n"
f"💎 Pick: {game['top_pick_type']} → {game['top_pick_value']} ({game['confidence']}%)"
    )

# =========================
# MAIN
# =========================
def main():

    print("📡 MIBOTMLB STARTED")

    games = fetch_mlb_games()
    if not games:
        send_telegram_message("⚠️ No hay juegos MLB hoy.")
        return

    analyzed_games, top_msg = analyze_games(games)

    # =========================
    # ENVIAR JUEGOS
    # =========================
    for game in analyzed_games:
        send_telegram_message(format_game(game))

    # =========================
    # GUARDAR PICKS TOP 5
    # =========================
    top5 = sorted(analyzed_games, key=lambda x: x["confidence"], reverse=True)[:5]

    for pick in top5:
        save_pick(
            pick["top_pick_game"],
            pick["top_pick_type"],
            pick["top_pick_value"]
        )

    # =========================
    # TOP 5 TELEGRAM
    # =========================
    send_telegram_message(top_msg)

    # =========================
    # GRADER AUTOMÁTICO
    # =========================
    try:
        grade_picks()
    except Exception as e:
        print("Grader error:", e)

    # =========================
    # REPORTE DIARIO
    # =========================
    report = daily_report()

    send_telegram_message(report)

# =========================
# LOOP PARA RAILWAY FREE
# =========================
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("Error main:", e)

        # Espera 1 hora antes de volver a ejecutar
        time.sleep(3600)
