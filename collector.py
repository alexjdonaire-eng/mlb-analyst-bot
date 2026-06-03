import os
import json
import requests
from datetime import datetime, timezone

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
    """Envía mensaje a Telegram con debug de errores"""
    if not TOKEN or not CHAT_ID:
        print("⚠️ Faltan variables de entorno TOKEN o CHAT_ID")
        return

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
        if r.status_code != 200:
            print("❌ Error enviando Telegram:", r.status_code, r.text)
        else:
            print("✅ Mensaje enviado a Telegram")
    except Exception as e:
        print("❌ Excepción enviando Telegram:", e)


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
        print("❌ Error obteniendo odds:", e)
        return []


# =========================
# HISTORIAL
# =========================

def load_last_snapshot():
    """Carga el último snapshot guardado"""
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            return json.loads(lines[-1])
    except FileNotFoundError:
        print("📂 No existe el archivo de historial, se creará uno nuevo")
        return {}
    except Exception as e:
        print("❌ Error leyendo historial:", e)
        return {}


def save_snapshot(data):
    """Guarda snapshot en archivo JSONL"""
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print("❌ Error guardando snapshot:", e)


# =========================
# MAIN
# =========================

def main():
    print("🚨 COLLECTOR STARTED")

    odds = get_odds()
    if not odds:
        send_telegram("⚠️ COLLECTOR: No se obtuvieron odds.")
        return

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys() if isinstance(last_snapshot, dict) else [])

    current_snapshot = {}
    saved = 0

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
                saved += 1

            current_snapshot[game_id] = snapshot

        except Exception as e:
            print("❌ Error procesando juego:", e)

    # Mensaje final a Telegram
    msg = f"✅ COLLECTOR RUN\n\nNew snapshots: {saved}\nGames found: {len(odds)}"
    send_telegram(msg)

    print("FINISHED")
    print(msg)


if __name__ == "__main__":
    main()
