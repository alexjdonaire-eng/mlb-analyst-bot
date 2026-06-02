import os
import requests
import time
from datetime import datetime, timezone

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# =========================
# FETCH ODDS SNAPSHOT
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
# EXTRACT MARKET PRICE
# =========================

def extract_prices(game):

    try:
        book = game["bookmakers"][0]
        outs = book["markets"][0]["outcomes"]

        return {o["name"]: o["price"] for o in outs}

    except:
        return {}

# =========================
# STEAM DETECTION (SIMPLIFIED)
# =========================

def detect_steam(prev, current):

    steam_signals = {}

    for team in current:

        if team in prev:

            change = prev[team] - current[team]

            # steam move threshold
            if change >= 0.15:
                steam_signals[team] = "STRONG SHARP MONEY"
            elif change >= 0.08:
                steam_signals[team] = "MODERATE SHARP ACTION"

    return steam_signals

# =========================
# IMPLIED PROBABILITY
# =========================

def implied_prob(price):

    return 1 / price if price else 0

# =========================
# MAIN SHARP ENGINE
# =========================

def main():

    print("🚀 V9 SHARP MONEY SYSTEM")

    snapshot1 = fetch_odds()

    time.sleep(120)  # esperar cambio de mercado

    snapshot2 = fetch_odds()

    report = "🏦 MLB V9 SHARP MONEY SYSTEM\n\n"

    for g1 in snapshot1:

        g2 = next((x for x in snapshot2 if x["id"] == g1["id"]), None)

        if not g2:
            continue

        p1 = extract_prices(g1)
        p2 = extract_prices(g2)

        steam = detect_steam(p1, p2)

        if not steam:
            continue

        home = g1.get("home_team")
        away = g1.get("away_team")

        report += f"⚾ {away} vs {home}\n"

        for team, signal in steam.items():
            report += f"💰 {team}: {signal}\n"

        # CLV simplified proxy
        if steam:
            report += "📊 CLV SIGNAL: POSITIVE MOMENTUM\n"

        report += "\n────────────────────\n\n"

    send(report)
    print("✅ V9 SENT")

if __name__ == "__main__":
    main()
