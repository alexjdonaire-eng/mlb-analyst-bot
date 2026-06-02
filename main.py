import os
import json
import requests
from datetime import datetime

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
API_KEY = os.getenv("ODDS_API_KEY")

HISTORY_FILE = "market_history.jsonl"

# =========================
# GET ODDS
# =========================

def get_odds():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    return r.json() if r.status_code == 200 else []

# =========================
# SAVE SNAPSHOT
# =========================

def save_snapshot(game_id, odds):

    data = {
        "time": datetime.utcnow().isoformat(),
        "game_id": game_id,
        "odds": odds
    }

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

# =========================
# COLLECT
# =========================

def main():

    odds = get_odds()

    for game in odds:

        try:

            book = game["bookmakers"][0]
            outs = book["markets"][0]["outcomes"]

            current = {}

            for o in outs:
                current[o["name"]] = o["price"]

            save_snapshot(game["id"], current)

            print("saved:", game["away_team"], "vs", game["home_team"])

        except:
            continue

if __name__ == "__main__":
    main()
