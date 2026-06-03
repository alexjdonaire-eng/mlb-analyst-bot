import os
import json
import requests
from datetime import datetime, timezone

# =========================
# VARIABLES DE ENTORNO
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

HISTORY_FILE = "market_history.jsonl"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=20
        )
        print("✅ Mensaje enviado a Telegram")
    except Exception as e:
        print("❌ Error enviando a Telegram:", e)

# =========================
# COLLECTOR
# =========================
def collector():
    print("🚨 COLLECTOR STARTED")
    try:
        r = requests.get(
            ODDS_URL,
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=30
        )
        if r.status_code != 200:
            raise Exception(f"Error en API Odds: {r.status_code} {r.text}")

        odds = r.json()
        print(f"⚾ {len(odds)} juegos encontrados")

        # Cargar última snapshot
        last_snapshot = {}
        try:
            with open(HISTORY_FILE, "r") as f:
                lines = f.readlines()
                if lines:
                    last_snapshot = json.loads(lines[-1])
        except:
            print("⚠️ No se encontró historial previo")

        last_ids = set(last_snapshot.keys() if last_snapshot else [])
        saved = 0
        current_snapshot = {}

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
                with open(HISTORY_FILE, "a") as f:
                    f.write(json.dumps(snapshot) + "\n")
                saved += 1

            current_snapshot[game_id] = snapshot

        msg = f"✅ COLLECTOR RUN\n\nNew snapshots: {saved}\nGames found: {len(odds)}"
        send_telegram(msg)
        print(msg)

        return current_snapshot

    except Exception as e:
        print("❌ ERROR EN COLLECTOR:", e)
        send_telegram(f"❌ ERROR EN COLLECTOR: {e}")
        return {}

# =========================
# ANALYZER
# =========================
def analyzer(history):
    print("🚨 ANALYZER STARTED")
    try:
        # Tomar última snapshot
        games = list(history.values())[-30:]  # Últimos 30 juegos
        if not games:
            send_telegram("⚠️ No hay datos para analizar")
            print("⚠️ No hay datos para analizar")
            return

        report = "🏦 MLB PREDICCIONES\n\n"
        total = 0

        for game in games:
            away = game.get("away_team")
            home = game.get("home_team")
            odds = game.get("odds", {})

            if len(odds) < 2:
                continue

            winner = min(odds, key=odds.get)
            prob = round((1 / odds[winner]) * 100, 1)

            if prob >= 65:
                confidence = "🔥 ALTA"
            elif prob >= 58:
                confidence = "✅ MEDIA"
            else:
                confidence = "⚠️ BAJA"

            report += (
                f"⚾ {away} vs {home}\n"
                f"🎯 Ganador: {winner} ({prob}%)\n"
                f"📊 Confianza: {confidence}\n"
                f"⭐ Mejor jugada: {winner}\n\n"
                f"────────────────────\n\n"
            )
            total += 1

        if total == 0:
            report = "⚠️ No hay suficientes datos todavía."

        send_telegram(report)
        print("✅ ANALYZER COMPLETADO")
        print(report)

    except Exception as e:
        print("❌ ERROR EN ANALYZER:", e)
        send_telegram(f"❌ ERROR EN ANALYZER: {e}")

# =========================
# MAIN
# =========================
def main():
    print("🚀 BOT STARTED")
    snapshot = collector()
    analyzer(snapshot)
    print("3. DONE")

if __name__ == "__main__":
    main()
