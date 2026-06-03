import os
import json
import requests
from datetime import datetime, UTC

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "market_history.jsonl"


# =========================
# TELEGRAM
# =========================

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
    except:
        pass


# =========================
# ODDS API
# =========================

def get_odds():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        },
        timeout=30
    )

    if r.status_code != 200:
        print("API ERROR:", r.status_code)
        return []

    return r.json()


# =========================
# SAVE SNAPSHOT
# =========================

def save_snapshot(snapshot):

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


# =========================
# COUNT SNAPSHOTS
# =========================

def count_snapshots():

    try:
        with open(HISTORY_FILE, "r") as f:
            return sum(1 for _ in f)
    except:
        return 0


# =========================
# MAIN
# =========================

def main():

    print("🚨 COLLECTOR STARTED")

    odds = get_odds()

    saved = 0

    for game in odds:

        try:

            if not game.get("bookmakers"):
                continue

            book = game["bookmakers"][0]

            if not book.get("markets"):
                continue

            snapshot = {
                "time": datetime.now(UTC).isoformat(),
                "game_id": game["id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "odds": {}
            }

            for outcome in book["markets"][0]["outcomes"]:
                snapshot["odds"][outcome["name"]] = outcome["price"]

            save_snapshot(snapshot)

            saved += 1

        except Exception as e:
            print("GAME ERROR:", e)

    total_snapshots = count_snapshots()

    send_telegram(
        f"✅ COLLECTOR RUN\n\n"
        f"New snapshots: {saved}\n"
        f"Games found: {len(odds)}\n"
        f"History size: {total_snapshots}"
    )

    print("NEW SNAPSHOTS:", saved)
    print("TOTAL SNAPSHOTS:", total_snapshots)
    print("FINISHED")


if __name__ == "__main__":
    main()
