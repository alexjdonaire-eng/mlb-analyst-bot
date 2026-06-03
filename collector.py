import os
import json
import requests
from datetime import datetime, timezone
import time

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
def send_telegram(msg, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg},
                timeout=20
            )
            if r.status_code == 200:
                print(f"✅ Telegram sent successfully")
                return True
            else:
                print(f"⚠️ Telegram returned status {r.status_code}: {r.text}")
        except Exception as e:
            print(f"❌ Telegram send attempt {attempt+1} failed: {e}")
        time.sleep(2)
    return False

# =========================
# FETCH ODDS
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
        r.raise_for_status()
        data = r.json()
        print(f"📊 Fetched {len(data)} games from Odds API")
        return data
    except Exception as e:
        print(f"❌ Failed to fetch odds: {e}")
        send_telegram(f"❌ Failed to fetch odds: {e}")
        return []

# =========================
# HISTORY
# =========================
def load_last_snapshot():
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            last = json.loads(lines[-1])
            print("📂 Last snapshot loaded")
            return last
    except FileNotFoundError:
        print("⚠️ History file not found, creating new one")
        return {}
    except Exception as e:
        print(f"❌ Failed to load last snapshot: {e}")
        return {}

def save_snapshot(data):
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        print(f"💾 Snapshot saved for game {data.get('game_id')}")
    except Exception as e:
        print(f"❌ Failed to save snapshot: {e}")
        send_telegram(f"❌ Failed to save snapshot: {e}")

# =========================
# MAIN
# =========================
def main():
    print("🚨 COLLECTOR STARTED")

    odds = get_odds()
    if not odds:
        print("⚠️ No odds fetched, exiting")
        return

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys() if isinstance(last_snapshot, dict) else [])

    current_snapshot = {}
    saved_count = 0

    for game in odds:
        try:
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
                "odds": {}
            }

            for o in book["markets"][0]["outcomes"]:
                snapshot["odds"][o["name"]] = o["price"]

            # Guardar solo si es nuevo
            if game_id not in last_ids:
                save_snapshot(snapshot)
                saved_count += 1

            current_snapshot[game_id] = snapshot
        except Exception as e:
            print(f"❌ Failed processing game {game.get('id')}: {e}")
    
    report = f"✅ COLLECTOR RUN\n\nNew snapshots: {saved_count}\nGames found: {len(odds)}"
    send_telegram(report)

    print("🏁 COLLECTOR FINISHED")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
