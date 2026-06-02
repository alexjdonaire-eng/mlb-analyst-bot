import os
import requests
import sqlite3
import time
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# DB SETUP
# =========================

conn = sqlite3.connect("odds.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS odds_snapshots (
    game_id TEXT,
    team TEXT,
    price REAL,
    timestamp INTEGER
)
""")

conn.commit()

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# =========================
# FETCH ODDS
# =========================

def fetch_odds():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    return r.json() if r.status_code == 200 else []

# =========================
# STORE SNAPSHOT
# =========================

def store_snapshot(game_id, team, price):

    cur.execute("""
        INSERT INTO odds_snapshots VALUES (?, ?, ?, ?)
    """, (game_id, team, price, int(time.time())))

    conn.commit()

# =========================
# GET OPEN PRICE (CLV BASE)
# =========================

def get_open_price(game_id, team):

    cur.execute("""
        SELECT price FROM odds_snapshots
        WHERE game_id=? AND team=?
        ORDER BY timestamp ASC
        LIMIT 1
    """, (game_id, team))

    row = cur.fetchone()

    return row[0] if row else None

# =========================
# GET LATEST PRICE
# =========================

def get_latest_price(game_id, team):

    cur.execute("""
        SELECT price FROM odds_snapshots
        WHERE game_id=? AND team=?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (game_id, team))

    row = cur.fetchone()

    return row[0] if row else None

# =========================
# STEAM SCORE
# =========================

def steam_score(open_price, current_price):

    if not open_price or not current_price:
        return 0

    return open_price - current_price

# =========================
# IMPLIED PROB
# =========================

def imp(price):
    return 1 / price if price else 0

# =========================
# MAIN V9 PRO ENGINE
# =========================

def main():

    print("🚀 V9 PRO SHARP SYSTEM")

    odds = fetch_odds()

    report = "🏦 MLB V9 PRO SHARP SYSTEM\n\n"

    for g in odds:

        game_id = g.get("id")
        home = g.get("home_team")
        away = g.get("away_team")

        try:
            book = g["bookmakers"][0]
            outs = book["markets"][0]["outcomes"]
        except:
            continue

        for o in outs:

            team = o["name"]
            price = o["price"]

            # guardar snapshot
            store_snapshot(game_id, team, price)

            open_p = get_open_price(game_id, team)
            current_p = get_latest_price(game_id, team)

            steam = steam_score(open_p, current_p)

            clv = None
            if open_p and current_p:
                clv = (imp(current_p) - imp(open_p)) * 100

            # SHARP DETECTION
            sharp_signal = ""

            if steam > 0.20:
                sharp_signal = "🔴 SHARP MONEY INCOMING"
            elif steam > 0.10:
                sharp_signal = "🟠 MODERATE STEAM"

            if sharp_signal:

                report += (
                    f"⚾ {away} vs {home}\n"
                    f"🎯 Team: {team}\n"
                    f"📉 Open: {open_p}\n"
                    f"📈 Now: {current_p}\n"
                    f"💰 Steam: {round(steam,3)}\n"
                    f"📊 CLV: {round(clv,2) if clv else 'N/A'}%\n"
                    f"{sharp_signal}\n\n"
                    f"────────────────────\n\n"
                )

    send(report)
    print("✅ V9 PRO DONE")

if __name__ == "__main__":
    main()
