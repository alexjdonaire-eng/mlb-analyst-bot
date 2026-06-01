import os
import requests
import math

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")


# =========================
# TELEGRAM
# =========================

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram env vars")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# MATH FUNCTIONS
# =========================

def prob(odds):
    if not odds:
        return 0
    return 1 / odds


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


def predict(team_a, team_b):
    a = ratings.get(team_a, 50)
    b = ratings.get(team_b, 50)

    diff = a - b

    prob_a = 1 / (1 + math.exp(-diff / 10))
    prob_b = 1 - prob_a

    return prob_a, prob_b


# =========================
# DATA FETCH
# =========================

def get_games():
    if not ODDS_API_KEY:
        print("Missing ODDS_API_KEY")
        return []

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        r = requests.get(URL, params=params, timeout=10)

        if r.status_code != 200:
            print("Odds API error:", r.status_code)
            return []

        return r.json()

    except Exception as e:
        print("API error:", e)
        return []


# =========================
# ANALYSIS
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
# MAIN
# =========================

def main():

    print("🚀 MLB BOT RUNNING...")

    games = get_games()

    if not games:
        send_message("❌ No se encontraron juegos o error API")
        return

    reporte = "⚾ MLB PICKS DEL DÍA ⚾\n\n"

    picks_count = 0

    for game in games:

        if not game.get("bookmakers"):
            continue

        home = game["home_team"]
        away = game["away_team"]

        book = game["bookmakers"][0]

        if not book.get("markets"):
            continue

        outcomes = book["markets"][0].get("outcomes", [])

        if not outcomes:
            continue

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            continue

        pick, edge = analyze_game(home, away, home_odds, away_odds)

        if edge < 0.10:
            continue

        picks_count += 1

        if picks_count > 5:
            break

        confidence = (
            "🔥 MUY ALTA" if edge >= 0.20 else
            "✅ ALTA" if edge >= 0.15 else
            "⚠️ MEDIA"
        )

        reporte += (
            f"{away} vs {home}\n"
            f"🎯 Pick: {pick}\n"
            f"📈 Edge: {round(edge*100,2)}%\n"
            f"📊 Confianza: {confidence}\n\n"
        )

    if picks_count == 0:
        send_message("❌ No hay picks con valor hoy")
    else:
        send_message(reporte)


if __name__ == "__main__":
    main()
