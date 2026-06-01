import os
import requests
from datetime import datetime
import math

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"


# =========================
# LOG SYSTEM
# =========================

def log(msg):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


# =========================
# TELEGRAM
# =========================

def send_message(text):
    if not TOKEN or not CHAT_ID:
        log("❌ Missing Telegram config")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        log(f"Telegram error: {e}")


# =========================
# MATH CORE
# =========================

def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(p1, p2):
    total = p1 + p2
    if total == 0:
        return 0, 0
    return p1 / total, p2 / total


def kelly(edge, odds):
    # versión simplificada (safe)
    if odds <= 1:
        return 0
    b = odds - 1
    return max(0, min(edge / b, 0.25))  # cap 25%


# =========================
# MODEL (ELO SIMPLE)
# =========================

ratings = {
    "Los Angeles Dodgers": 60,
    "New York Yankees": 58,
    "Philadelphia Phillies": 57,
    "Atlanta Braves": 57,
    "Houston Astros": 56,
    "Detroit Tigers": 55,
    "Minnesota Twins": 54,
    "Milwaukee Brewers": 54,
    "Tampa Bay Rays": 53,
    "San Francisco Giants": 52,
    "Seattle Mariners": 52,
    "Arizona Diamondbacks": 52,
    "San Diego Padres": 52,
    "Kansas City Royals": 50,
    "Texas Rangers": 50,
    "Cleveland Guardians": 50,
    "Cincinnati Reds": 48,
    "Los Angeles Angels": 47,
    "St. Louis Cardinals": 47,
    "Washington Nationals": 46,
    "Miami Marlins": 45,
    "Pittsburgh Pirates": 45,
    "Athletics": 44,
    "Toronto Blue Jays": 44,
    "New York Mets": 44,
    "Boston Red Sox": 43,
    "Chicago Cubs": 43,
    "Baltimore Orioles": 43,
    "Colorado Rockies": 40,
    "Chicago White Sox": 38
}


def predict(home, away):
    a = ratings.get(home, 50)
    b = ratings.get(away, 50)

    diff = a - b

    p_home = 1 / (1 + math.exp(-diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# GAME ENGINE
# =========================

def analyze_game(home, away, home_odds, away_odds):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    m_home, m_away = predict(home, away)

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return home, edge_home, home_odds, m_home, p_home
    else:
        return away, edge_away, away_odds, m_away, p_away


# =========================
# MAIN
# =========================

def main():

    log("🚀 TRADING BOT STARTED")

    try:
        r = requests.get(
            URL,
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=10
        )
    except Exception as e:
        log(f"API ERROR: {e}")
        return

    if r.status_code != 200:
        log(f"API FAIL: {r.text}")
        return

    games = r.json()
    log(f"📦 Games: {len(games)}")

    for game in games:

        home = game.get("home_team")
        away = game.get("away_team")

        if not game.get("bookmakers"):
            continue

        book = game["bookmakers"][0]
        outcomes = book["markets"][0].get("outcomes", [])

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o.get("name") == home:
                home_odds = o.get("price")
            if o.get("name") == away:
                away_odds = o.get("price")

        if not home_odds or not away_odds:
            continue

        pick, edge, odds, model_prob, market_prob = analyze_game(
            home, away, home_odds, away_odds
        )

        edge_pct = edge * 100

        log(f"{away} vs {home} | Edge: {round(edge_pct,2)}%")

        if edge < 0.08:
            continue

        # Kelly sizing
        stake = kelly(edge, odds)

        confidence = (
            "🔥 HIGH" if edge > 0.20 else
            "✅ MED" if edge > 0.12 else
            "⚠️ LOW"
        )

        # =========================
        # 📩 ONE MESSAGE PER GAME
        # =========================

        message = f"""⚾ MLB TRADING ALERT

{away} vs {home}

🎯 PICK: {pick}
📊 Edge: {round(edge_pct,2)}%
📈 Model: {round(model_prob*100,2)}%
📉 Market: {round(market_prob*100,2)}%

💰 Odds: {odds}
🧠 Confidence: {confidence}
📦 Stake (Kelly): {round(stake*100,2)}%

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(message)
        log("📩 Sent game alert")


# =========================
# START
# =========================

if __name__ == "__main__":
    main()
