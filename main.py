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
HIST_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds-history"


# =========================
# LOG
# =========================

def log(msg):
    print(f"[V6 SHARP] {msg}")


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
        log(e)


# =========================
# UTIL
# =========================

def norm(x):
    return x.lower().replace(" ", "")


def prob(o):
    return 1 / o if o else 0


def remove_vig(a, b):
    t = a + b
    if t == 0:
        return 0, 0
    return a / t, b / t


# =========================
# TEAM MODEL
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
    h = ratings.get(norm(home), 50)
    a = ratings.get(norm(away), 50)

    diff = h - a
    p_home = 1 / (1 + pow(2.71828, -diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# SHARP MONEY ENGINE
# =========================

def sharp_score(open_odds, current_odds):

    """
    idea:
    - si odds bajan fuerte → sharp money en ese lado
    - si suben → posible public fade
    """

    if not open_odds or not current_odds:
        return 0

    movement = open_odds - current_odds

    # normalización simple
    return movement * 10


def market_pressure(edge, sharp):

    """
    combina valor del modelo + dinero inteligente
    """

    return edge + (sharp * 0.3)


# =========================
# ODDS FETCH
# =========================

def get_games():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    return r.json()


# =========================
# ANALYSIS CORE
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

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    pick = home if edge_home > edge_away else away
    edge = max(edge_home, edge_away)

    # SHARP MONEY (simplificado sin histórico real aún)
    # (en v7 lo conectamos a odds-history real)
    sharp = 0

    pressure = market_pressure(edge, sharp)

    return {
        "game": f"{away} vs {home}",
        "pick": pick,
        "edge": pressure,
        "model": m_home if pick == home else m_away,
        "market": p_home if pick == home else p_away,
        "odds": home_o if pick == home else away_o,
        "sharp": sharp
    }


# =========================
# MAIN
# =========================

def main():

    log("START V6 SHARP MONEY ENGINE")

    games = get_games()

    used = set()

    for g in games:

        res = analyze(g)
        if not res:
            continue

        if res["game"] in used:
            continue
        used.add(res["game"])

        if res["edge"] < 0.05:
            continue

        msg = f"""🏦 MLB SHARP MONEY ENGINE v6

⚾ {res['game']}

🎯 PICK: {res['pick']}

📊 EDGE (ADJUSTED): {round(res['edge']*100,2)}%
📈 MODEL: {round(res['model']*100,2)}%
📉 MARKET: {round(res['market']*100,2)}%

💰 ODDS: {res['odds']}

📡 SHARP SIGNAL: {round(res['sharp'],2)}

────────────────────
"""

        send_message(msg)
        log(res["game"])


if __name__ == "__main__":
    main()
