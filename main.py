import os
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_URL = "https://statsapi.mlb.com/api/v1/schedule"


# =========================
# LOG
# =========================

def log(msg):
    print(f"[LOG] {msg}")


# =========================
# TELEGRAM
# =========================

def send_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except:
        pass


# =========================
# NORMALIZE
# =========================

def normalize(x):
    return x.lower().replace(" ", "")


# =========================
# PROBABILIDAD
# =========================

def prob(o):
    return 1 / o if o else 0


def remove_vig(a, b):
    t = a + b
    if t == 0:
        return 0, 0
    return a / t, b / t


# =========================
# MODELO SIMPLE
# =========================

ratings = {
    "losangelesdodgers": 60,
    "newyorkyankees": 58,
    "atlantabraves": 57,
    "houstonastros": 56,
    "detroittigers": 55,
    "minnesotatwins": 54,
    "seattlemariners": 52,
    "arizonadiamondbacks": 52,
    "sandiegopadres": 52,
    "texasrangers": 50,
    "torontobluejays": 44,
    "newyorkmets": 44,
    "chicagowhitesox": 38
}


def model(home, away):
    h = ratings.get(normalize(home), 50)
    a = ratings.get(normalize(away), 50)

    diff = h - a

    p_home = 1 / (1 + (2.71828 ** (-diff / 10)))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# PITCHERS + ERA REAL
# =========================

def get_pitchers():

    pitchers = {}

    try:
        url = MLB_URL + f"?sportId=1&date={datetime.utcnow().strftime('%Y-%m-%d')}&hydrate=probablePitcher"
        data = requests.get(url, timeout=10).json()

        games = data.get("dates", [])[0].get("games", [])

        for g in games:

            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            def extract(p):
                if not p:
                    return ("TBA", None)

                name = p.get("fullName", "TBA")
                era = p.get("stats", {}).get("pitching", {}).get("era", None)

                return (name, era)

            ap = extract(g["teams"]["away"].get("probablePitcher"))
            hp = extract(g["teams"]["home"].get("probablePitcher"))

            pitchers[(normalize(away), normalize(home))] = {
                "away_name": ap[0],
                "away_era": ap[1],
                "home_name": hp[0],
                "home_era": hp[1],
                "source": "MLB"
            }

    except:
        pass

    return pitchers


def get_pitch(pitchers, away, home):

    return pitchers.get(
        (normalize(away), normalize(home)),
        {
            "away_name": "TBA",
            "away_era": None,
            "home_name": "TBA",
            "home_era": None,
            "source": "NONE"
        }
    )


# =========================
# DATA QUALITY
# =========================

def dq(p):
    score = 100

    if p["away_name"] == "TBA":
        score -= 30
    if p["home_name"] == "TBA":
        score -= 30

    return max(score, 0)


def dq_label(s):
    if s >= 80:
        return "🟢 CONFIABLE"
    if s >= 50:
        return "🟡 PARCIAL"
    return "🔴 BAJA"


# =========================
# ANALYSIS
# =========================

def analyze(game, pitchers):

    home = game["home_team"]
    away = game["away_team"]

    if not game.get("bookmakers"):
        return None

    book = game["bookmakers"][0]
    outs = book["markets"][0]["outcomes"]

    home_o = away_o = None

    for o in outs:
        if o["name"] == home:
            home_o = o["price"]
        if o["name"] == away:
            away_o = o["price"]

    if not home_o or not away_o:
        return None

    p_home = prob(home_o)
    p_away = prob(away_o)

    p_home, p_away = remove_vig(p_home, p_away)

    pitch = get_pitch(pitchers, away, home)

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
            "odds": home_o,
            "pitch": pitch
        }
    else:
        return {
            "game": f"{away} vs {home}",
            "pick": away,
            "edge": edge_away,
            "model": m_away,
            "market": p_away,
            "odds": away_o,
            "pitch": pitch
        }


# =========================
# MAIN
# =========================

def main():

    log("HEDGE FUND v3.1 START")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
    )

    games = r.json()
    pitchers = get_pitchers()

    seen = set()

    for g in games:

        # 🔥 FILTRO REAL DE HOY
        if today not in g.get("commence_time", ""):
            continue

        res = analyze(g, pitchers)
        if not res:
            continue

        if res["game"] in seen:
            continue
        seen.add(res["game"])

        p = res["pitch"]
        dq_score = dq(p)

        if dq_score < 40:
            continue

        message = f"""🏦 MLB SHARP ALERT (HEDGE FUND v3.1)

⚾ {res['game']}

🎯 PICK: {res['pick']}

📊 EDGE: {round(res['edge']*100,2)}%
📈 MODEL: {round(res['model']*100,2)}%
📉 MARKET: {round(res['market']*100,2)}%

💰 ODDS: {res['odds']}

🔥 PITCHERS:
- Away: {p['away_name']} ({p['away_era']})
- Home: {p['home_name']} ({p['home_era']})

🧠 DATA QUALITY: {dq_score}/100 → {dq_label(dq_score)}

────────────────────
"""

        send_message(message)
        log(res["game"])


if __name__ == "__main__":
    main()
