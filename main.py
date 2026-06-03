import os
import requests
from datetime import datetime
from analyzer import generate_report  # tu función que genera los picks

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# FUNCIONES
# =========================
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload)
    return response.status_code, response.text

def format_game(game):
    # Score balanceado según V5.11
    pitcher_component = game.get("pitcher_score", 0)
    market_component = game.get("market_move", 0) * -0.15
    steam_component = 2 if game.get("steam") == "🔥 SHARP MONEY IN" else -1 if game.get("steam") == "⚪ PUBLIC HEAVY" else 0
    score = round(50 + pitcher_component + market_component + steam_component, 2)
    
    # Nivel según score
    if score >= 70:
        level = "🔥 ELITE"
    elif score >= 60:
        level = "✅ STRONG"
    else:
        level = "⚠️ LEAN"
    
    # Evitar picks débiles
    pick_text = game.get("pick") if abs(score - 50) >= 2 else "NO BET"

    # Pitchers
    home_pitcher = game.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
    away_pitcher = game.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})

    message = (
        f"⚾ {game.get('home_team')} vs {game.get('away_team')}\n\n"
        f"🎯 Pick: {pick_text}\n"
        f"📊 Confianza: {game.get('confidence', 50)}%\n"
        f"📈 Edge: {game.get('edge', 0)}%\n"
        f"📡 Steam: {game.get('steam', '⚪ NEUTRAL')}\n"
        f"📉 Market Move: {game.get('market_move', 0)}\n"
        f"🧾 Pitchers: {home_pitcher['name']} (ERA {home_pitcher['ERA']}, WHIP {home_pitcher['WHIP']}) "
        f"vs {away_pitcher['name']} (ERA {away_pitcher['ERA']}, WHIP {away_pitcher['WHIP']})\n"
        f"🧠 Score: {score}\n"
        f"🏷 Nivel: {level}\n"
        f"━━━━━━━━━━━━━━"
    )
    return message

def main():
    print("🔥 MLB SHARP MONEY V5.11 FULL PRO START")
    games = generate_report()  # devuelve lista de dicts con los datos de cada juego
    if not games:
        print("❌ No games loaded")
        return

    for game in games:
        msg = format_game(game)
        status_code, text = send_telegram(msg)
        print(f"Sent: {game.get('home_team')} vs {game.get('away_team')} -> Status: {status_code}")

    print("🏦 MLB SHARP MONEY V5.11 FULL PRO COMPLETED")

# =========================
if __name__ == "__main__":
    main()
