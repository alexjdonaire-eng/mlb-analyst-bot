import os
import requests
import json
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

STORE_FILE = "store.json"


# =========================
# STORAGE (CLEAN STATE)
# =========================

def load_store():
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_store(data):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f)


# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )


# =========================
# DATA FETCH
# =========================

def get_games():
    r = requests.get(URL, params={
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    })

    if r.status_code != 200:
        return []

    return r.json()


# =========================
# FILTER TODAY GAMES
# =========================

def is_today(game):
    try:
        date_str = game["commence_time"][:10]
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return date_str == today
    except:
        return False


# =========================
# SIMPLE MODEL (TU CORE)
# =========================

def pick_model(game):

    home = game["home_team"]
    away = game["away_team"]

    # modelo placeholder (tu v6 entra aquí luego)
    pick = home

    return pick


# =========================
# GET ODDS FROM GAME
# =========================

def extract_odds(game, team):
    try:
        book = game["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]

        for o in outcomes:
            if o["name"] == team:
                return o["price"]
    except:
        pass

    return None


# =========================
# CLV ENGINE (REAL FIX)
# =========================

def calc_clv(stored_odds, current_odds):

    if not stored_odds or not current_odds:
        return None

    return (stored_odds - current_odds) / current_odds


# =========================
# MAIN
# =========================

def main():

    print("🚀 V7.1 CLV ENGINE RUNNING")

    games = get_games()
    store = load_store()

    report = "🏦 MLB CLV ENGINE v7.1\n\n"

    today_games = 0

    for game in games:

        if not is_today(game):
            continue

        today_games += 1

        game_id = game.get("id")

        if not game_id:
            continue

        home = game["home_team"]
        away = game["away_team"]

        pick = pick_model(game)

        current_odds = extract_odds(game, pick)

        # =========================
        # NEW GAME (STORE SNAPSHOT)
        # =========================

        if game_id not in store:

            store[game_id] = {
                "game": f"{away} vs {home}",
                "pick": pick,
                "odds_snapshot": current_odds,
                "timestamp": datetime.utcnow().isoformat()
            }

            send(f"🏦 NEW PICK\n⚾ {away} vs {home}\n🎯 {pick}\n💰 Odds: {current_odds}")

        # =========================
        # CLV CHECK (UPDATE)
        # =========================

        stored = store[game_id]

        clv = calc_clv(stored["odds_snapshot"], current_odds)

        status = "🟢 EDGE REAL" if clv and clv > 0 else "🔴 NO EDGE"

        report += (
            f"⚾ {stored['game']}\n"
            f"🎯 Pick: {stored['pick']}\n"
            f"📊 CLV: {round(clv*100,2) if clv else 0}%\n"
            f"{status}\n\n"
        )

    save_store(store)

    report = f"📊 JUEGOS HOY: {today_games}\n\n" + report

    send(report)


if __name__ == "__main__":
    main()
