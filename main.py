import os
import requests
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

# =========================
# DATA FETCH
# =========================

def get_games():
    r = requests.get(
        URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    if r.status_code != 200:
        print("ERROR:", r.text)
        return []

    return r.json()

# =========================
# FILTER TODAY (TEMPORAL)
# =========================

def is_today(game):

    try:

        game_time = datetime.fromisoformat(
            game["commence_time"].replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)

        hours_until = (game_time - now).total_seconds() / 3600

        return -6 <= hours_until <= 24

    except:
        return False

# =========================
# SIMPLE MODEL
# =========================

def pick_model(game):

    home = game["home_team"]
    away = game["away_team"]

    try:
        book = game["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]

        home_odds = None
        away_odds = None

        for o in outcomes:

            if o["name"] == home:
                home_odds = o["price"]

            if o["name"] == away:
                away_odds = o["price"]

        if home_odds and away_odds:

            if home_odds <= away_odds:
                return home
            else:
                return away

    except:
        pass

    return home

# =========================
# MAIN
# =========================

def main():

    print("🚀 MLB FOUNDATION STABLE V7.2 DIAGNOSTIC")

    games = get_games()

    print("TOTAL API GAMES:", len(games))

    report = "🏦 MLB QUANT ALERT\n\n"

    total_games = 0

    seen_games = set()

    for game in games:

        print(
            game.get("away_team"),
            "vs",
            game.get("home_team"),
            "-",
            game.get("commence_time")
        )

        if not is_today(game):
            continue

        game_id = game.get("id")

        if not game_id:
            continue

        if game_id in seen_games:
            continue

        seen_games.add(game_id)

        away = game["away_team"]
        home = game["home_team"]

        pick = pick_model(game)

        total_games += 1

        report += (
            f"⚾ {away} vs {home}\n\n"
            f"🎯 Ganador: {pick}\n\n"
            f"────────────────────\n\n"
        )

    report = (
        f"📊 Juegos encontrados: {total_games}\n\n"
        + report
    )

    send(report)

    print("✅ Reporte enviado")

if __name__ == "__main__":
    main()
