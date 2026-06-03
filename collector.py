import os
import json
import requests
from datetime import datetime, timezone

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "market_history.jsonl"

def send_telegram(msg):
    """Envía mensaje a Telegram con manejo de errores"""
    try:
        print(f"📨 Enviando Telegram: {msg[:50]}...")
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
    except Exception as e:
        print("❌ Error enviando a Telegram:", e)

def get_odds():
    """Obtiene probabilidades desde la API"""
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
        print(f"⚡ Odds obtenidas: {len(data)} juegos")
        return data
    except Exception as e:
        print("❌ Error al obtener odds:", e)
        send_telegram("❌ Collector ERROR al obtener odds")
        return []

def load_last_snapshot():
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            return json.loads(lines[-1])
    except Exception as e:
        print("⚠️ No se pudo cargar snapshot:", e)
        return {}

def save_snapshot(data):
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        print(f"💾 Snapshot guardado: {data['home_team']} vs {data['away_team']}")
    except Exception as e:
        print("❌ Error guardando snapshot:", e)
        send_telegram("❌ Collector ERROR guardando snapshot")

def main():
    print("🚨 COLLECTOR STARTED")
    send_telegram("🚨 Collector started")

    odds = get_odds()
    if not odds:
        send_telegram("⚠️ No se obtuvieron juegos")
        return

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys() if last_snapshot else [])

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
            "time": datetime.now(timezone.utc).isoformat(),
            "game_id": game_id,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "odds": {o["name"]: o["price"] for o in book["markets"][0]["outcomes"]}
        }

        if game_id not in last_ids:
            save_snapshot(snapshot)
            saved += 1

        current_snapshot[game_id] = snapshot

    msg = f"✅ COLLECTOR RUN\n\nNew snapshots: {saved}\nGames found: {len(odds)}"
    print(msg)
    send_telegram(msg)
    print("🚨 COLLECTOR FINISHED")

if __name__ == "__main__":
    main()
