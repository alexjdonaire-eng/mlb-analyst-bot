import os
import requests
from datetime import datetime
from analyzer import run_analyzer  # tu función que genera picks con pitchers reales

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# FUNCIONES TELEGRAM
# =========================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

# =========================
# FORMATEO JUEGO
# =========================
def format_game(game):
    home = game.get("home_team", "TBD")
    away = game.get("away_team", "TBD")
    pick = game.get("pick", "TBD")
    confidence = game.get("confidence", 0)
    edge = game.get("edge", 0)
    steam = game.get("steam", "NEUTRAL")
    market_move = game.get("market_move", "N/A")
    score = game.get("score", 0)
    level = game.get("level", "LEAN")

    # Pitchers reales
    home_pitcher = game.get("home_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})
    away_pitcher = game.get("away_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})
    pitchers_info = f"{home_pitcher['name']} (ERA {home_pitcher['ERA']}, WHIP {home_pitcher['WHIP']}) vs {away_pitcher['name']} (ERA {away_pitcher['ERA']}, WHIP {away_pitcher['WHIP']})"

    text = (
        f"⚾ {home} vs {away}\n\n"
        f"🎯 Pick: {pick}\n"
        f"📊 Confianza: {confidence:.2f}%\n"
        f"📈 Edge: {edge:.2f}%\n"
        f"📡 Steam: {steam}\n"
        f"📉 Market Move: {market_move}\n"
        f"🧾 Pitchers: {pitchers_info}\n"
        f"🧠 Score: {score:.2f}\n"
        f"🏷 Nivel: {level}\n"
        "━━━━━━━━━━━━━━"
    )
    return text

# =========================
# MAIN
# =========================
def main():
    print("🔥 ANALYZER VERSION V5.10 FULL PRO START")
    try:
        # run_analyzer retorna lista de juegos con toda la info
        games = run_analyzer()
    except Exception as e:
        print(f"❌ Error analizando juegos: {e}")
        games = []

    if not games:
        print("❌ No hay juegos para reportar")
        return

    # Enviar cada juego por Telegram
    for game in games:
        message = format_game(game)
        send_telegram_message(message)
        print(f"✅ Enviado a Telegram: {game.get('home_team', 'TBD')} vs {game.get('away_team', 'TBD')}")

    # Top 5 picks
    top5 = sorted(games, key=lambda x: x.get("confidence", 0), reverse=True)[:5]
    top5_text = "🔥 TOP 5 PICKS\n\n"
    for i, g in enumerate(top5, start=1):
        top5_text += f"{i}️⃣ {g.get('pick', 'TBD')} ({g.get('confidence',0):.2f}%)\n"
    send_telegram_message(top5_text)

    print("🏦 MLB SHARP MONEY V5.10 FULL PRO COMPLETED")

if __name__ == "__main__":
    main()
