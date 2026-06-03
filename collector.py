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
# TELEGRAM CON DEBUG Y REINTENTOS
# =========================
def send_telegram(msg, retries=3):
    for attempt in range(retries):
        try:
            print(f"📤 Enviando Telegram (Intento {attempt+1})...")
            resp = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg},
                timeout=20
            )
            if resp.status_code == 200:
                print("✅ Telegram enviado correctamente")
                return True
            else:
                print(f"⚠️ Telegram no enviado, status_code={resp.status_code}")
        except Exception as e:
            print(f"⚠️ Error enviando Telegram: {e}")
        time.sleep(2)
    print("❌ No se pudo enviar el mensaje a Telegram")
    return False

# =========================
# OBTENER ODDS DESDE API
# =========================
def get_odds():
    try:
        print("🌐 Solicitando odds a la API...")
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
        print(f"✅ Recibidos {len(data)} juegos")
        return data
    except Exception as e:
        print(f"⚠️ Error al obtener odds: {e}")
        return []

# =========================
# CARGAR ULTIMO SNAPSHOT
# =========================
def load_last_snapshot():
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            last = json.loads(lines[-1])
            print("📂 Último snapshot cargado")
            return last
    except FileNotFoundError:
        print("📂 Archivo de historial no encontrado, se creará uno nuevo")
        return {}
    except Exception as e:
        print(f"⚠️ Error cargando snapshot: {e}")
        return {}

# =========================
# GUARDAR SNAPSHOT
# =========================
def save_snapshot(data):
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        print(f"💾 Snapshot guardado: {data['game_id']}")
    except Exception as e:
        print(f"⚠️ Error guardando snapshot: {e}")

# =========================
# MAIN
# =========================
def main():
    print("🚨 COLLECTOR STARTED")
    
    odds = get_odds()
    if not odds:
        send_telegram("⚠️ COLLECTOR ERROR: No se pudieron obtener odds")
        return

    last_snapshot = load_last_snapshot()
    last_ids = set(last_snapshot.keys()) if last_snapshot else set()

    current_snapshot = {}
    saved_count = 0

    for game in odds:
        try:
            game_id = game.get("id")
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            bookmakers = game.get("bookmakers", [])

            if not game_id or not home_team or not away_team or not bookmakers:
                print(f"⚠️ Juego ignorado (datos incompletos): {game}")
                continue

            book = bookmakers[0]
            markets = book.get("markets", [])
            if not markets:
                print(f"⚠️ No hay markets para {home_team} vs {away_team}")
                continue

            snapshot = {
                "time": datetime.now(timezone.utc).isoformat(),
                "game_id": game_id,
                "home_team": home_team,
                "away_team": away_team,
                "odds": {}
            }

            for o in markets[0]["outcomes"]:
                snapshot["odds"][o["name"]] = o["price"]

            # Solo guardar si es nuevo o cambió
            if game_id not in last_ids:
                save_snapshot(snapshot)
                saved_count += 1

            current_snapshot[game_id] = snapshot

        except Exception as e:
            print(f"⚠️ Error procesando juego: {e}")

    msg = f"✅ COLLECTOR RUN\n\nNew snapshots: {saved_count}\nGames found: {len(odds)}"
    send_telegram(msg)
    print("🚨 COLLECTOR FINISHED")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
