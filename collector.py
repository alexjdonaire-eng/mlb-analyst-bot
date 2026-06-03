import os
import json
import requests
from datetime import datetime, timezone

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
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
        if r.status_code != 200:
            print("⚠️ Telegram error:", r.text)
    except Exception as e:
        print("⚠️ Telegram exception:", e)

# =========================
# FETCH ODDS
# =========================
def fetch_odds():
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
        if r.status_code != 200:
            print("⚠️ Odds API error:", r.status_code, r.text)
            return []
        data = r.json()
        print(f"📊 Fetched {len(data)} games from Odds API")
        return data
    except Exception as e:
        print("⚠️ Odds fetch exception:", e)
        return []

# =========================
# LOAD LAST SNAPSHOT
# =========================
def load_last_snapshot():
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            return json.loads(lines[-1])
    except Exception as e:
        print("⚠️ Load snapshot exception:", e)
        return {}

# =========================
# SAVE SNAPSHOT
# =========================
def save_snapshot(snapshot):
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(snapshot) + "\n")
    except Exception as e:
        print("⚠️ Save snapshot exception:", e)

# =========================
# MAIN COLLECTOR
# =========================
def main():
    print("🚨 COLLECTOR STARTED")
    send_telegram("🚨 COLLECTOR STARTED")  # debug guarantee

    odds_data = fetch_odds()
    if not odds_data:
        send_telegram("⚠️ No data fetched from Odds API")
        return

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys()) if last_snapshot else set()

    saved = 0
    current_snapshot = {}

    for game in odds_data:
        if not game.get("bookmakers"):
            continue
        book = game["bookmakers"][0]
        if not book.get("markets"):
            continue

        game_id = game["id"]
        snapshot = {
            "time": datetime.now(timezone.utc).isoformat(),
            "game_id": game_id,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "odds": {o["name"]: o["price"] for o in book["markets"][0]["outcomes"]}
        }

        current_snapshot[game_id] = snapshot

        if game_id not in last_ids:
            save_snapshot(snapshot)
            saved += 1

    msg = f"✅ COLLECTOR RUN\nNew snapshots: {saved}\nTotal games fetched: {len(odds_data)}"
    print(msg)
    send_telegram(msg)
    print("FINISHED")

if __name__ == "__main__":
    main()
