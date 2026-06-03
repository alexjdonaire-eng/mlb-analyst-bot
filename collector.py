import os
import json
import requests
from datetime import datetime, timezone

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "market_history.jsonl"

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
    except:
        pass

def get_odds():
    try:
        r = requests.get(
            ODDS_URL,
            params={
                "apiKey": API_KEY,
                "regions": "us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=20
        )
        return r.json()
    except:
        return []

def save_snapshot(snapshot):
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

def main():
    print("🚨 COLLECTOR START")

    odds = get_odds()
    if not odds:
        print("NO ODDS")
        return

    saved = 0

    for game in odds:
        try:
            book = game["bookmakers"][0]
            snapshot = {
                "time": datetime.now(timezone.utc).isoformat(),
                "game_id": game["id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "odds": {}
            }

            for o in book["markets"][0]["outcomes"]:
                snapshot["odds"][o["name"]] = o["price"]

            save_snapshot(snapshot)
            saved += 1

        except:
            continue

    print("Snapshots:", saved)
    send(f"✅ COLLECTOR RUN\nSnapshots: {saved}")

if __name__ == "__main__":
    main()
