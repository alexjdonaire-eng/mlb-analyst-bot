import os
import requests
from analyzer import run as run_analyzer
from collector import run as run_collector

# =========================
# CONFIG TELEGRAM
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM SENDER
# =========================
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return None

# =========================
# FORMAT GAME MESSAGE
# =========================
def format_game(game):

    home = game.get("home_team", "TBD")
    away = game.get("away_team", "TBD")

    pick = game.get("pick", "NO BET")
    confidence = game.get("confidence", 0)
    edge = game.get("edge", 0)

    steam = game.get("steam", "⚪ NEUTRAL")
    market = game.get("market_move", 0)

    home_p = game.get("home_pitcher", {})
    away_p = game.get("away_pitcher", {})

    score = game.get("score", 0)
    level = game.get("level", "⚠️ LEAN")

    message = (
        f"⚾ {away} vs {home}\n\n"
        f"🎯 Pick: {pick}\n"
        f"📊 Confianza: {confidence:.2f}%\n"
        f"📈 Edge: {edge:.2f}%\n"
        f"📡 Steam: {steam}\n"
        f"📉 Market Move: {market}\n"
        f"🧾 Pitchers: "
        f"{away_p.get('name','TBD')} (ERA {away_p.get('ERA','-')}, WHIP {away_p.get('WHIP','-')}) "
        f"vs "
        f"{home_p.get('name','TBD')} (ERA {home_p.get('ERA','-')}, WHIP {home_p.get('WHIP','-')})\n"
        f"🧠 Score: {score}\n"
        f"🏷 Nivel: {level}\n"
        f"━━━━━━━━━━━━━━"
    )

    return message

# =========================
# MAIN PIPELINE
# =========================
def main():

    print("🔥 MLB SHARP MONEY V5.11 FULL PRO START")

    # 1. COLLECT DATA
    games = run_collector()

    if not games:
        print("❌ No games loaded")
        return

    # 2. ANALYZE DATA
    results = run_analyzer(games)

    if not results:
        print("❌ No analysis results")
        return

    # 3. SEND EACH GAME SEPARATELY
    for game in results:
        msg = format_game(game)
        status = send_telegram(msg)

        print(f"📤 Sent {game.get('away_team')} vs {game.get('home_team')} -> {status}")

    print("🏁 CYCLE COMPLETE V5.11")

# =========================
if __name__ == "__main__":
    main()
