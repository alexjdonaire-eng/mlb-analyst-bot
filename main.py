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
    print(f"[HEDGE FUND v4] {msg}")


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
# UTIL
# =========================

def normalize(x):
    return x.lower().replace(" ", "")


def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(a, b):
    total = a + b
    if total == 0:
        return 0, 0
    return a / total, b / total


# =========================
# MARKET MODEL (CORE ONLY)
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
    "chicagowhitesox": 38,
    "milwaukeebrewers": 51,
    "stlouiscardinals": 47
}


def model(home, away):
    h = ratings.get(normalize(home), 50)
    a = ratings.get(normalize(away), 50)

    diff = h - a

    # logistic simplificada (market-neutral base)
    p_home = 1 / (1 + pow(2.71828, -diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# PITCHERS (VERIFICATION ONLY)
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

            def parse(p):
                if not p:
                    return ("TBA", None)

                name = p.get("fullName", "TBA")
                era = p.get("stats", {}).get("pitching", {}).get("era", None)

                return (name, era)

            ap = parse(g["teams"]["away"].get("probablePitcher"))
            hp = parse(g["teams"]["home"].get("probablePitcher"))

            pitchers[(normalize(away), normalize(home))] = {
                "away_name": ap[0],
                "away_era": ap[1],
                "home_name": hp[0],
                "home_era": hp[1]
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
            "home_era": None
        }
    )


# =========================
# EDGE ENGINE
# =========================

def compute_edge(market_prob, model_prob):
    return model_prob - market_prob


# =========================
# ANALYZER
# =========================

def analyze(game):

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

    m_home, m_away = model(home, away)

    edge_home = compute_edge(p_home, m_home)
    edge_away = compute_edge(p_away, m_away)

    if edge_home > edge_away:
        return {
            "game": f"{away} vs {home}",
            "pick": home,
            "edge": edge_home,
            "model": m_home,
            "market": p_home,
            "odds": home_o
        }
    else:
        return {
            "game": f"{away} vs {home}",
            "pick": away,
            "edge": edge_away,
            "model": m_away,
            "market": p_away,
            "odds": away_o
        }


# =========================
# MAIN
# =========================

def main():

    log("STARTING V4 INSTITUTIONAL CORE")

    today = datetime.utcnow().strftime("%Y-%m-%d")

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

    used = set()

    for g in games:

        # filtro simple de hoy (evita basura histórica)
        if today not in g.get("commence_time", ""):
            continue

        res = analyze(g)
        if not res:
            continue

        if res["game"] in used:
            continue
        used.add(res["game"])

        pitch = get_pitch(pitchers, *res["game"].split(" vs ")[::-1])

        # filtro institucional de edge
        if res["edge"] < 0.05:
            continue

        msg = f"""🏦 MLB HEDGE FUND v4 (INSTITUTIONAL CORE)

⚾ {res['game']}

🎯 PICK: {res['pick']}

📊 EDGE: {round(res['edge']*100,2)}%
📈 MODEL: {round(res['model']*100,2)}%
📉 MARKET: {round(res['market']*100,2)}%

💰 ODDS: {res['odds']}

🔥 PITCHERS (VERIFICATION ONLY):
- Away: {pitch['away_name']} ({pitch['away_era']})
- Home: {pitch['home_name']} ({pitch['home_era']})

🧠 MODE: MARKET-DRIVEN (NO NOISE)

────────────────────
"""

        send_message(msg)
        log(res["game"])


if __name__ == "__main__":
    main()
