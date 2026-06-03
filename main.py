import os
import requests
from analyzer import run_analyzer  # tu función que genera los picks
from datetime import datetime

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# FUNCIONES
# =========================
def send_telegram(message: str):
    """Envía un mensaje a Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Error enviando Telegram: {response.text}")
    return response

def format_game(game: dict) -> str:
    """Formatea un juego para Telegram con pitchers y stats."""
    pitcher_home = game.get("pitcher_home", {"name":"TBD", "ERA":"-", "WHIP":"-"})
    pitcher_away = game.get("pitcher_away", {"name":"TBD", "ERA":"-", "WHIP":"-"})

    message = (
        f"⚾ {game['away_team']} vs {game['home_team']}\n\n"
        f"🎯 Pick: {game['pick']}\n"
        f"📊 Confianza: {game['confidence']}%\n"
        f"📈 Edge: {game['edge']}%\n"
        f"📡 Steam: {game.get('steam','⚪ NEUTRAL')}\n"
        f"🧾 Pitchers: {pitcher_away['name']} (ERA: {pitcher_away['ERA']}, WHIP: {pitcher_away['WHIP']}) "
        f"vs {pitcher_home['name']} (ERA: {pitcher_home['ERA']}, WHIP: {pitcher_home['WHIP']})\n"
        f"🧠 Score: {game.get('score','-')}\n"
        f"🏷 Nivel: {game.get('level','⚠️ LEAN')}\n"
        f"━━━━━━━━━━━━━━"
    )
    return message

# =========================
# MAIN
# =========================
def main():
    print(f"🏦 MLB SHARP MONEY V5.7 START - {datetime.now()}")

    # Obtener los juegos procesados por analyzer
    try:
        games = run_analyzer()  # devuelve lista de dicts de juegos
        print(f"📊 Games loaded: {len(games)}")
    except Exception as e:
        print(f"Error corriendo analyzer: {e}")
        return

    # Enviar cada juego por Telegram
    for game in games:
        try:
            message = format_game(game)
            send_telegram(message)
            print(f"✅ Telegram sent: {game['away_team']} vs {game['home_team']}")
        except Exception as e:
            print(f"Error enviando juego {game['away_team']} vs {game['home_team']}: {e}")

    # Top picks combinada
    top_picks = sorted(games, key=lambda x: x['confidence'], reverse=True)[:4]
    comb_message = "💎 COMBINADA DEL DÍA\n\n" + "\n".join([f"✅ {g['pick']}" for g in top_picks])
    comb_message += f"\n\n🔥 Mejor Pick:\n{top_picks[0]['pick']} ({top_picks[0]['confidence']}%)"
    send_telegram(comb_message)
    print("🏁 Combinada enviada")

if __name__ == "__main__":
    main()
