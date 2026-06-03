import os
import requests

from analyzer import run_analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload, timeout=20)
    except Exception as e:
        print(f"Telegram error: {e}")


def format_game(game):

    hp = game.get("home_pitcher", {})
    ap = game.get("away_pitcher", {})

    home_team = game.get("home_team", "N/A")
    away_team = game.get("away_team", "N/A")

    winner = game.get("pick", "N/A")
    confidence = game.get("confidence", 0)

    total_pick = game.get("total_pick", "N/A")
    total_confidence = game.get("total_confidence", 0)

    runline_pick = game.get("runline_pick", "N/A")
    runline_confidence = game.get("runline_confidence", 0)

    level = game.get("level", "⚠️ LEAN")

    recommended = game.get(
        "recommended_play",
        winner
    )

    message = (
        f"⚾ {away_team} vs {home_team}\n\n"

        f"🧾 Lanzadores:\n"
        f"{home_team}: {hp.get('name','TBD')} "
        f"(ERA {hp.get('ERA','-')} | "
        f"WHIP {hp.get('WHIP','-')})\n"

        f"{away_team}: {ap.get('name','TBD')} "
        f"(ERA {ap.get('ERA','-')} | "
        f"WHIP {ap.get('WHIP','-')})\n\n"

        f"🎯 Ganador: {winner} ({confidence}%)\n"
        f"⚾ Total carreras: {total_pick} ({total_confidence}%)\n"
        f"⚾ Hándicap: {runline_pick} ({runline_confidence}%)\n\n"

        f"🏷 Nivel: {level}\n"
        f"💎 Jugada recomendada: {recommended}"
    )

    return message


def main():

    print("🏦 MLB BOT V5.13 START")

    report = run_analyzer()

    if not report:
        print("❌ No hay picks")
        return

    for game in report:

        try:

            msg = format_game(game)

            send_telegram(msg)

            print(
                f"✅ Enviado: "
                f"{game.get('away_team')} vs "
                f"{game.get('home_team')}"
            )

        except Exception as e:

            print(f"❌ Error enviando juego: {e}")

    print("🚀 Todos los juegos enviados")


if __name__ == "__main__":
    main()
