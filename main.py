import os
import requests
from analyzer import run_analyzer

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# =========================
# FUNCIONES
# =========================
def send_telegram(message: str):
    """Envía un mensaje a Telegram."""
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(TELEGRAM_URL, data=payload)
        if response.status_code != 200:
            print(f"❌ Error Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Excepción Telegram: {e}")


def format_game(game: dict) -> str:
    """Formatea la información de cada juego para Telegram."""
    return (
        f"⚾ {game['home_team']} vs {game['away_team']}\n\n"
        f"🎯 Pick: {game['pick']}\n"
        f"📊 Confianza: {game['confidence']}%\n"
        f"📈 Edge: {game['edge']}%\n"
        f"📡 Steam: {game['steam']}\n"
        f"📉 Market Move: {game['market_move']}\n"
        f"🧾 Pitchers: {game['home_pitcher']['name']} (ERA {game['home_pitcher']['ERA']}, WHIP {game['home_pitcher']['WHIP']}) "
        f"vs {game['away_pitcher']['name']} (ERA {game['away_pitcher']['ERA']}, WHIP {game['away_pitcher']['WHIP']})\n"
        f"🧠 Score: {game['score']}\n"
        f"🏷 Nivel: {game['level']}\n"
        f"━━━━━━━━━━━━━━"
    )


# =========================
# MAIN
# =========================
def main():
    print("🔥 MLB SHARP MONEY V5.11 FULL PRO START")

    results = run_analyzer()

    if not results:
        print("❌ No analysis results")
        return

    for game in results:
        msg = format_game(game)
        send_telegram(msg)

    print("🏁 CYCLE COMPLETE")


if __name__ == "__main__":
    main()
