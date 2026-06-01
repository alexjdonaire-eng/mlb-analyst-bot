import os
import requests
from datetime import datetime, timezone
import math

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date="


# =========================
# LOGS
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
# PROBABILITY MODEL
# =========================

def predict(home, away):
    a = ratings.get(home, 50)
    b = ratings.get(away, 50)

    diff = a - b
    p_home = 1 / (1 + math.exp(-diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total


# =========================
# PITCHERS SYSTEM (FIXED)
# =========================

def get_pitcher_map():

    try:
        url = MLB_SCHEDULE_URL + datetime.utcnow().strftime("%Y-%m-%d")
        r = requests.get(url, timeout=10)
        data = r.json()
    except:
        return {}

    pitcher_map = {}

    try:
        games = data.get("dates", [])[0].get("games", [])

        for g in games:

            home_team = g["teams"]["home"]["team"]["name"]
            away_team = g["teams"]["away"]["team"]["name"]

            home_pitcher = g["teams"]["home"].get("probablePitcher", {})
            away_pitcher = g["teams"]["away"].get("probablePitcher", {})

            home_name = home_pitcher.get("fullName", "TBD")
            away_name = away_pitcher.get("fullName", "TBD")

            home_era = 4.20
            away_era = 4.20

            try:
                home_era = float(
                    home_pitcher.get("stats", [{}])[0]
                    .get("splits", [{}])[0]
                    .get("stat", {}).get("era", 4.2)
                )
            except:
                pass

            try:
                away_era = float(
                    away_pitcher.get("stats", [{}])[0]
                    .get("splits", [{}])[0]
                    .get("stat", {}).get("era", 4.2)
                )
            except:
                pass

            pitcher_map[(away_team, home_team)] = {
                "away_pitcher": away_name,
                "home_pitcher": home_name,
                "away_era": away_era,
                "home_era": home_era
            }

    except:
        pass

    return pitcher_map


# =========================
# ANALYSIS ENGINE
# =========================

def analyze(home, away, home_odds, away_odds, pitchers):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    m_home, m_away = predict(home, away)

    # pitcher adjustment
    key = (away, home)
    pitch = pitchers.get(key, None)

    if pitch:
        home_adj = 1 / (pitch["home_era"] + 1)
        away_adj = 1 / (pitch["away_era"] + 1)
    else:
        home_adj = away_adj = 1

    m_home *= home_adj
    m_away *= away_adj

    total = m_home + m_away
    m_home /= total
    m_away /= total

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return home, edge_home, m_home, p_home, pitch
    else:
        return away, edge_away, m_away, p_away, pitch


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
        },
        timeout=10
    )

    games = r.json()
    log(f"📦 Games loaded: {len(games)}")

    pitchers = get_pitcher_map()

    seen = set()
    all_picks = []

    for game in games:

        home = game.get("home_team")
        away = game.get("away_team")

        if not home or not away:
            continue

        key = f"{away}_vs_{home}"

        if key in seen:
            continue
        seen.add(key)

        if not game.get("bookmakers"):
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

        pick, edge, model_p, market_p, pitch = analyze(
            home, away, home_odds, away_odds, pitchers
        )

        all_picks.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "edge": edge,
            "model": model_p,
            "market": market_p,
            "pitch": pitch
        })

    # sort by edge
    all_picks.sort(key=lambda x: x["edge"], reverse=True)

    log(f"🏁 Total picks: {len(all_picks)}")

    # =========================
    # SEND TOP PICKS
    # =========================

    for p in all_picks[:6]:

        if p["edge"] < 0.06:
            continue

        pitch = p["pitch"]

        if pitch:
            pitcher_line = f"🔥 Pitcher: {pitch['away_pitcher']} ({pitch['away_era']}) vs {pitch['home_pitcher']} ({pitch['home_era']})"
        else:
            pitcher_line = "🔥 Pitcher: TBD vs TBD"

        message = f"""⚾ SHARP MLB ALERT

{p['game']}

🎯 PICK: {p['pick']}
📊 Edge: {round(p['edge']*100,2)}%
📈 Model: {round(p['model']*100,2)}%
📉 Market: {round(p['market']*100,2)}

{pitcher_line}

🧠 SHARP MODE PRO
🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(message)
        log(f"📩 SENT: {p['game']}")


if __name__ == "__main__":
    main()
