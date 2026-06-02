import os
import json
import requests
from datetime import datetime, UTC

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "market_history.jsonl"


def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
    except:
        pass


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
        return []

    return r.json()


def load_last_snapshot():
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            return json.loads(lines[-1])
    except:
        return {}


def save_snapshot(data):
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


def main():

    print("🚨 COLLECTOR STARTED")

    odds = get_odds()

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys())

    current_snapshot = {}

    saved = 0

    for game in odds:

        if not game.get("bookmakers"):
            continue

        book = game["bookmakers"][0]
        if not book.get("markets"):
            continue

        game_id = game["id"]

        snapshot = {
            "time": datetime.now(UTC).isoformat(),
            "game_id": game_id,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "odds": {}
        }

        for o in book["markets"][0]["outcomes"]:
            snapshot["odds"][o["name"]] = o["price"]

        # SOLO guardar si cambió o es nuevo
        if game_id not in last_ids:
            save_snapshot(snapshot)
            saved += 1

        current_snapshot[game_id] = snapshot

    send_telegram(
        f"✅ COLLECTOR RUN\n\nNew snapshots: {saved}\nGames found: {len(odds)}"
    )

    print("FINISHED")


if __name__ == "__main__":
    main()
