import os
import requests

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"


# =========================
# TELEGRAM
# =========================

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram env variables")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# DATA UTILS
# =========================

def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(p1, p2):
    total = p1 + p2
    if total == 0:
        return 0, 0
    return p1 / total, p2 / total


# =========================
# MLB MODEL (ELO SIMPLE)
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
    import math

    a = ratings.get(home, 50)
    b = ratings.get(away, 50)

    diff = a - b

    p_home = 1 / (1 + math.exp(-diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# ANALYZER
# =========================

def analyze_game(home, away, home_odds, away_odds):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    m_home, m_away = predict(home, away)

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return home, edge_home
    else:
        return away, edge_away


# =========================
# MAIN BOT
# =========================

def main():

    print("🚀 MLB BOT RUNNING")

    if not ODDS_API_KEY:
        send_message("❌ Missing ODDS_API_KEY")
        return

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
        send_message(f"❌ API error: {e}")
        return

    if r.status_code != 200:
        send_message("❌ Error fetching odds API")
        return

    games = r.json()

    if not games:
        send_message("❌ No games found today")
        return

    reporte = "⚾ MLB PICKS DEL DÍA ⚾\n\n"
    picks_count = 0

    for game in games:

        home = game.get("home_team")
        away = game.get("away_team")

        if not home or not away:
            continue

        if not game.get("bookmakers"):
            continue

        book = game["bookmakers"][0]

        if not book.get("markets"):
            continue

        outcomes = book["markets"][0].get("outcomes", [])

        if not outcomes:
            continue

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o.get("name") == home:
                home_odds = o.get("price")
            if o.get("name") == away:
                away_odds = o.get("price")

        if not home_odds or not away_odds:
            continue

        pick, edge = analyze_game(home, away, home_odds, away_odds)

        if edge < 0.10:
            continue

        picks_count += 1

        reporte += (
            f"{away} vs {home}\n"
            f"🎯 Pick: {pick}\n"
            f"📈 Edge: {round(edge * 100, 2)}%\n\n"
        )

    if picks_count == 0:
        send_message("❌ No value picks today")
    else:
        send_message(reporte)


if __name__ == "__main__":
    main()
