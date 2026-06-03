import os
import requests
from analyzer import analyze_games, format_games_message

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# FETCH GAMES (ROBUSTO)
# =========================
def fetch_games():
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal"
        }

        resp = requests.get(ODDS_URL, params=params, timeout=25)

        print("STATUS:", resp.status_code)

        try:
            data = resp.json()
        except:
            print("ERROR JSON INVALID")
            return []

        if not isinstance(data, list):
            print("API ERROR:", data)
            return []

        print(f"📊 Games loaded: {len(data)}")
        return data

    except Exception as e:
        print("FETCH ERROR:", e)
        return []

# =========================
# TELEGRAM SEND
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print("Telegram error:", e)

# =========================
# MAIN
# =========================
def main():
    print("🚀 MIBOT MLB V8 PRO START")

    games = fetch_games()

    if not games:
        send_telegram("⚠️ No hay juegos disponibles o error en la API")
        return

    analyzed = analyze_games(games)

    # enviar en bloques de 4 juegos (limpio Telegram)
    batch = 4
    for i in range(0, len(analyzed), batch):
        chunk = analyzed[i:i+batch]
        msg = format_games_message(chunk)
        send_telegram(msg)

    # TOP PICKS separados
    winners = [g["winner_line"] for g in analyzed if g["confidence"] >= 60]
    totals = [g["total_line"] for g in analyzed if g["confidence"] >= 60]
    spreads = [g["spread_line"] for g in analyzed if g["confidence"] >= 60]

    if winners:
        send_telegram("<b>🔥 TOP PICKS GANADOR</b>\n" + "\n".join(winners[:5]))

    if totals:
        send_telegram("<b>🔥 TOP PICKS TOTALES</b>\n" + "\n".join(totals[:5]))

    if spreads:
        send_telegram("<b>🔥 TOP PICKS HÁNDICAP</b>\n" + "\n".join(spreads[:5]))

if __name__ == "__main__":
    main()
