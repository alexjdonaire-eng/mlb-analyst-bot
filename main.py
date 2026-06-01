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
# LOGGING
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
# NORMALIZE
# =========================

def normalize(name):
    return name.lower().replace(" ", "").replace(".", "")


# =========================
# RATING MODEL
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
    if total == 0:
        return 0, 0
    return p1 / total, p2 / total


# =========================
# DATA QUALITY ENGINE
# =========================

def data_quality(game, pitch):

    score = 100

    if not game.get("bookmakers"):
        return 0

    if not game.get("home_team") or not game.get("away_team"):
        return 0

    # pitchers
    if not pitch:
        score -= 40
    else:
        if pitch["away_pitcher"] == "TBA":
            score -= 20
        if pitch["home_pitcher"] == "TBA":
            score -= 20

    return max(score, 0)


def confidence(score):

    if score >= 80:
        return "🟢 FULL TRUST"
    elif score >= 50:
        return "🟡 PARTIAL TRUST"
    return "🔴 BLOCKED"


# =========================
# PITCHERS (SAFE MODE)
# =========================

def get_pitchers():

    url = MLB_URL + datetime.utcnow().strftime("%Y-%m-%d")

    try:
        data = requests.get(url, timeout=10).json()
    except:
        return {}

    pitchers = {}

    try:
        games = data.get("dates", [])[0].get("games", [])

        for g in games:

            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            home_p = g["teams"]["home"].get("probablePitcher")
            away_p = g["teams"]["away"].get("probablePitcher")

            def safe(p):
                if not p:
                    return "TBA"
                return p.get("fullName", "TBA")

            home_name = safe(home_p)
            away_name = safe(away_p)

            pitchers[(normalize(away), normalize(home))] = {
                "away_pitcher": away_name,
                "home_pitcher": home_name
            }

    except:
        pass

    return pitchers


def find_pitchers(pitchers, away, home):

    return pitchers.get(
        (normalize(away), normalize(home)),
        {
            "away_pitcher": "TBA",
            "home_pitcher": "TBA"
        }
    )


# =========================
# SHARP MONEY ENGINE
# =========================

def sharp_signal(pick, home_odds, away_odds):

    try:
        if home_odds < away_odds:
            return "📉 MARKET FAVORING HOME"
        elif away_odds < home_odds:
            return "📉 MARKET FAVORING AWAY"
    except:
        pass

    return "⚖️ NO CLEAR FLOW"


# =========================
# MODEL
# =========================

def model(home, away):

    h = ratings.get(normalize(home), 50)
    a = ratings.get(normalize(away), 50)

    diff = h - a
    p_home = 1 / (1 + math.exp(-diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# ANALYSIS
# =========================

def analyze(game, pitchers):

    home = game.get("home_team")
    away = game.get("away_team")

    book = game["bookmakers"][0]
    outcomes = book["markets"][0]["outcomes"]

    home_odds = away_odds = None

    for o in outcomes:
        if o["name"] == home:
            home_odds = o["price"]
        if o["name"] == away:
            away_odds = o["price"]

    if not home_odds or not away_odds:
        return None

    p_home = prob(home_odds)
    p_away = prob(away_odds)
    p_home, p_away = remove_vig(p_home, p_away)

    pitch = find_pitchers(pitchers, away, home)

    m_home, m_away = model(home, away)

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return {
            "game": f"{away} vs {home}",
            "pick": home,
            "edge": edge_home,
            "model": m_home,
            "market": p_home,
            "pitch": pitch,
            "odds": home_odds
        }
    else:
        return {
            "game": f"{away} vs {home}",
            "pick": away,
            "edge": edge_away,
            "model": m_away,
            "market": p_away,
            "pitch": pitch,
            "odds": away_odds
        }


# =========================
# MAIN
# =========================

def main():

    log("🏦 MLB QUANT FUND v1 STARTED")

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

    results = []

    for game in games:

        if not game.get("bookmakers"):
            continue

        res = analyze(game, pitchers)

        if not res:
            continue

        dq = data_quality(game, res["pitch"])

        if dq < 50:
            continue

        results.append({
            **res,
            "dq": dq
        })

    results.sort(key=lambda x: x["edge"], reverse=True)

    log(f"PICKS FOUND: {len(results)}")

    for r in results[:5]:

        pitch = r["pitch"]

        message = f"""🏦 MLB QUANT FUND v1

{r['game']}

🎯 PICK: {r['pick']}
📊 EDGE: {round(r['edge']*100,2)}%
📈 MODEL: {round(r['model']*100,2)}%
📉 MARKET: {round(r['market']*100,2)}

🔥 ODDS: {r['odds']}
🔥 PITCHERS: {pitch['away_pitcher']} vs {pitch['home_pitcher']}

🧪 DATA QUALITY: {r['dq']}/100 → {confidence(r['dq'])}
⚡ SHARP SIGNAL: {sharp_signal(r['pick'], r['model'], r['market'])}

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(message)
        log(f"SENT: {r['game']}")


if __name__ == "__main__":
    main()
