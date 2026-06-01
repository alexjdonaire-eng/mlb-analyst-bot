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

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date="


# =========================
# LOGS
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
# NORMALIZATION
# =========================

def normalize(name):
    return name.lower().replace(" ", "").replace(".", "")


# =========================
# MODEL (TEAM STRENGTH)
# =========================

ratings = {
    "losangelesdodgers": 60,
    "newyorkyankees": 58,
    "philadelphiaphillies": 57,
    "atlantabraves": 57,
    "houstonastros": 56,
    "detroittigers": 55,
    "minnesotatwins": 54,
    "milwaukeebrewers": 54,
    "tampabayrays": 53,
    "sanfranciscogiants": 52,
    "seattlemariners": 52,
    "arizonadiamondbacks": 52,
    "sandiegopadres": 52,
    "kansascityroyals": 50,
    "texasrangers": 50,
    "clevelandguardians": 50,
    "cincinnatireds": 48,
    "losangelesangels": 47,
    "stlouiscardinals": 47,
    "washingtonnationals": 46,
    "miamimarlins": 45,
    "pittsburghpirates": 45,
    "athletics": 44,
    "torontobluejays": 44,
    "newyorkmets": 44,
    "bostonredsox": 43,
    "chicagocubs": 43,
    "baltimoreorioles": 43,
    "coloradorockies": 40,
    "chicagowhitesox": 38
}


# =========================
# PROBABILITY
# =========================

def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total


# =========================
# PITCHER ENGINE (INSTITUTIONAL MATCH)
# =========================

def get_pitchers():

    url = MLB_URL + datetime.utcnow().strftime("%Y-%m-%d")

    try:
        data = requests.get(url, timeout=10).json()
    except:
        return {}

    pitcher_map = {}

    try:
        games = data.get("dates", [])[0].get("games", [])

        for g in games:

            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            home_p = g["teams"]["home"].get("probablePitcher", {})
            away_p = g["teams"]["away"].get("probablePitcher", {})

            home_name = home_p.get("fullName", "TBD")
            away_name = away_p.get("fullName", "TBD")

            home_era = 4.2
            away_era = 4.2

            try:
                home_era = float(home_p.get("stats", [{}])[0]
                                 .get("splits", [{}])[0]
                                 .get("stat", {}).get("era", 4.2))
            except:
                pass

            try:
                away_era = float(away_p.get("stats", [{}])[0]
                                 .get("splits", [{}])[0]
                                 .get("stat", {}).get("era", 4.2))
            except:
                pass

            pitcher_map[(normalize(away), normalize(home))] = {
                "away_pitcher": away_name,
                "home_pitcher": home_name,
                "away_era": away_era,
                "home_era": home_era
            }

    except:
        pass

    return pitcher_map


def find_pitchers(pitchers, away, home):

    key = (normalize(away), normalize(home))

    if key in pitchers:
        return pitchers[key]

    return {
        "away_pitcher": "TBD",
        "home_pitcher": "TBD",
        "away_era": 4.2,
        "home_era": 4.2
    }


# =========================
# SHARP MODEL CORE
# =========================

def model(home, away, pitch):

    h = ratings.get(normalize(home), 50)
    a = ratings.get(normalize(away), 50)

    # team probability
    diff = h - a
    team_p_home = 1 / (1 + math.exp(-diff / 10))
    team_p_away = 1 - team_p_home

    # pitcher impact (inverse ERA)
    home_pitch = 1 / (pitch["home_era"] + 1)
    away_pitch = 1 / (pitch["away_era"] + 1)

    # weighted blend
    p_home = (team_p_home * 0.65) + (home_pitch * 0.35)
    p_away = (team_p_away * 0.65) + (away_pitch * 0.35)

    total = p_home + p_away
    return p_home / total, p_away / total


# =========================
# ANALYSIS
# =========================

def analyze(home, away, home_odds, away_odds, pitchers):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    pitch = find_pitchers(pitchers, away, home)

    m_home, m_away = model(home, away, pitch)

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

    log("🚀 SHARP INSTITUTIONAL BOT STARTED")

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    games = r.json()
    pitchers = get_pitchers()

    seen = set()
    results = []

    for game in games:

        home = game.get("home_team")
        away = game.get("away_team")

        if not home or not away:
            continue

        key = f"{away}_{home}"
        if key in seen:
            continue
        seen.add(key)

        if not game.get("bookmakers"):
            continue

        outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]

        home_odds = away_odds = None

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

        results.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "edge": edge,
            "model": model_p,
            "market": market_p,
            "pitch": pitch
        })

    results.sort(key=lambda x: x["edge"], reverse=True)

    log(f"📊 PICKS FOUND: {len(results)}")

    for r in results[:5]:

        if r["edge"] < 0.06:
            continue

        p = r["pitch"]

        message = f"""🏦 MLB SHARP INSTITUTIONAL ALERT

{r['game']}

🎯 PICK: {r['pick']}
📊 EDGE: {round(r['edge']*100,2)}%
📈 MODEL: {round(r['model']*100,2)}%
📉 MARKET: {round(r['market']*100,2)}

🔥 PITCHERS:
{p['away_pitcher']} ({p['away_era']}) vs {p['home_pitcher']} ({p['home_era']})

🧠 SHARP LEVEL: INSTITUTIONAL
🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(message)
        log(f"SENT: {r['game']}")


if __name__ == "__main__":
    main()
