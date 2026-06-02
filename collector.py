import os
import json
import requests
from datetime import datetime, UTC

# =========================
# CONFIG
# =========================

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "market_history.jsonl"

# =========================
# TELEGRAM
# =========================

def send_telegram(msg):

    print("TOKEN EXISTS:", bool(TOKEN))
    print("CHAT_ID EXISTS:", bool(CHAT_ID))

    try:

        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=20
        )

        print("TELEGRAM STATUS:", r.status_code)
        print("TELEGRAM RESPONSE:", r.text)

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================
# GET ODDS
# =========================

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
            timeout=30
        )

        print("ODDS STATUS:", r.status_code)

        if r.status_code != 200:
            print(r.text)
            return []

        return r.json()

    except Exception as e:

        print("ODDS ERROR:", e)
        return []

# =========================
# SAVE SNAPSHOT
# =========================

def save_snapshot(game_id, odds):

    snapshot = {
        "time": datetime.now(UTC).isoformat(),
        "game_id": game_id,
        "odds": odds
    }

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

# =========================
# MAIN
# =========================

def main():

    print("🚨 COLLECTOR VISIBLE TEST 🚨")

    odds = get_odds()

    print("GAMES FOUND:", len(odds))

    saved = 0

    for game in odds:

        try:

            if not game.get("bookmakers"):
                continue

            book = game["bookmakers"][0]

            if not book.get("markets"):
                continue

            outs = book["markets"][0]["outcomes"]

            current = {}

            for o in outs:
                current[o["name"]] = o["price"]

            save_snapshot(game["id"], current)

            print(
                f"SAVED: {game['away_team']} vs {game['home_team']}"
            )

            saved += 1

        except Exception as e:

            print("GAME ERROR:", e)

    send_telegram(
        f"✅ COLLECTOR RUN\n\nGames processed: {saved}"
    )

    print("FINISHED")

if __name__ == "__main__":
    main()
