import os
import requests
from datetime import datetime, timezone
import math

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
PITCHERS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date="


# =========================
# LOG SYSTEM
# =========================

def log(msg):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


# =========================
# TELEGRAM
# =========================

def send_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        log(f"Telegram error: {e}")


# =========================
# MATH MODEL
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


# =========================
# MODEL
# =========================

def predict(home, away):
    a = ratings.get(home, 50)
    b = ratings.get(away, 50)

    diff = a - b
    p_home = 1 / (1 + math.exp(-diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


def prob(odds):
    return 1 / odds


def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total


# =========================
# PITCHER FETCH (REAL MLB API)
# =========================

def get_pitchers():
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + datetime.utcnow().strftime("%Y-%m-%d")
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return None


def extract_pitchers(data, home, away):
    try:
        games = data.get("dates", [])[0].get("games", [])
        for g in games:
            teams = g["teams"]
            home_p = teams["home"]["probablePitcher"]["fullName"]
            away_p = teams["away"]["probablePitcher"]["fullName"]
            home_era = teams["home"]["probablePitcher"]["stats"][0]["splits"][0]["stat"]["era"]
            away_era = teams["away"]["probablePitcher"]["stats"][0]["splits"][0]["stat"]["era"]

            return {
                "home_pitcher": home_p,
                "away_pitcher": away_p,
                "home_era": float(home_era),
                "away_era": float(away_era)
            }
    except:
        return {
            "home_pitcher": "TBD",
            "away_pitcher": "TBD",
            "home_era": 4.20,
            "away_era": 4.20
        }


# =========================
# EDGE ENGINE (SHARP)
# =========================

def analyze(home, away, home_odds, away_odds, pitchers):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    m_home, m_away = predict(home, away)

    # pitcher adjustment (VERY IMPORTANT)
    home_adj = 1 / (pitchers["home_era"] + 1)
    away_adj = 1 / (pitchers["away_era"] + 1)

    m_home *= home_adj
    m_away *= away_adj

    total = m_home + m_away
    m_home /= total
    m_away /= total

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return home, edge_home, m_home, p_home, pitchers["home_pitcher"], pitchers["home_era"]
    else:
        return away, edge_away, m_away, p_away, pitchers["away_pitcher"], pitchers["away_era"]


# =========================
# MAIN
# =========================

def main():

    log("🚀 SHARP MODE PRO STARTED")

    r = requests.get(
        URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    games = r.json()
    log(f"📦 Games loaded: {len(games)}")

    pitcher_data = get_pitchers()

    all_picks = []

    for game in games:

        home = game["home_team"]
        away = game["away_team"]

        if not game["bookmakers"]:
            continue

        book = game["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            continue

        pitchers = extract_pitchers(pitcher_data, home, away)

        pick, edge, model_p, market_p, pitcher, era = analyze(
            home, away, home_odds, away_odds, pitchers
        )

        all_picks.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "edge": edge,
            "model": model_p,
            "market": market_p,
            "pitcher": pitcher,
            "era": era
        })

    # =========================
    # RANK PICKS (SHARP STYLE)
    # =========================

    all_picks.sort(key=lambda x: x["edge"], reverse=True)

    log(f"🏁 Total picks: {len(all_picks)}")

    # send TOP 6 ONLY (sharp constraint)
    for p in all_picks[:6]:

        if p["edge"] < 0.06:
            continue

        message = f"""⚾ SHARP MLB ALERT

{p['game']}

🎯 PICK: {p['pick']}
📊 Edge: {round(p['edge']*100,2)}%
📈 Model: {round(p['model']*100,2)}%
📉 Market: {round(p['market']*100,2)}

🔥 Pitcher: {p['pitcher']}
📊 ERA: {p['era']}

🧠 SHARP MODE PRO
🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(message)
        log(f"📩 SENT: {p['game']}")


if __name__ == "__main__":
    main()
