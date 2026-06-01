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
MLB_SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER = "https://statsapi.mlb.com/api/v1/people/{id}/stats"


# =========================
# LOG
# =========================

def log(msg):
    print(f"[V5] {msg}")


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
# TEAM MODEL (BASE)
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
# PITCHER ENGINE (REAL STATS)
# =========================

pitch_cache = {}


def get_pitcher_stats(player_id):

    if not player_id:
        return None

    if player_id in pitch_cache:
        return pitch_cache[player_id]

    try:
        url = MLB_PLAYER.format(id=player_id) + "?stats=season&group=pitching"
        data = requests.get(url, timeout=10).json()

        splits = data.get("stats", [])[0].get("splits", [])
        if not splits:
            return None

        stats = splits[0]["stat"]

        era = float(stats.get("era", 0))
        whip = float(stats.get("whip", 0))
        k9 = float(stats.get("strikeoutsPer9Inn", 0))

        result = {
            "era": era,
            "whip": whip,
            "k9": k9
        }

        pitch_cache[player_id] = result
        return result

    except:
        return None


def pitcher_impact(stats):

    if not stats:
        return 0

    # modelo simple cuant:
    # ERA alto = negativo
    # WHIP alto = negativo
    # K9 alto = positivo

    impact = 0

    impact += (4.00 - stats["era"]) * 2.5
    impact += (1.30 - stats["whip"]) * 3.0
    impact += (stats["k9"] - 8.0) * 1.5

    return impact / 10


# =========================
# PITCHERS FROM MLB
# =========================

def get_pitchers():

    pitchers = {}

    try:
        url = MLB_SCHEDULE + f"?sportId=1&date={datetime.utcnow().strftime('%Y-%m-%d')}&hydrate=probablePitcher"
        data = requests.get(url, timeout=10).json()

        games = data.get("dates", [])[0].get("games", [])

        for g in games:

            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            def parse(p):
                if not p:
                    return None, None

                return p.get("id"), p.get("fullName")

            ap_id, ap_name = parse(g["teams"]["away"].get("probablePitcher"))
            hp_id, hp_name = parse(g["teams"]["home"].get("probablePitcher"))

            pitchers[(norm(away), norm(home))] = {
                "away_id": ap_id,
                "away_name": ap_name or "TBA",
                "home_id": hp_id,
                "home_name": hp_name or "TBA"
            }

    except:
        pass

    return pitchers


def get_pitch(pitchers, away, home):

    return pitchers.get(
        (norm(away), norm(home)),
        {
            "away_id": None,
            "away_name": "TBA",
            "home_id": None,
            "home_name": "TBA"
        }
    )


# =========================
# EDGE ENGINE (TEAM + PITCHER)
# =========================

def compute_edge(team_p, model_p, pitcher_adj):
    return (model_p + pitcher_adj) - team_p


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

    m_home, m_away = model(home, away)

    pitch = get_pitch(pitchers, away, home)

    away_stats = get_pitcher_stats(pitch["away_id"])
    home_stats = get_pitcher_stats(pitch["home_id"])

    away_adj = pitcher_impact(away_stats)
    home_adj = pitcher_impact(home_stats)

    edge_home = compute_edge(p_home, m_home, home_adj)
    edge_away = compute_edge(p_away, m_away, away_adj)

    if edge_home > edge_away:
        return {
            "game": f"{away} vs {home}",
            "pick": home,
            "edge": edge_home,
            "model": m_home,
            "market": p_home,
            "odds": home_o,
            "pitch": pitch,
            "stats": home_stats
        }
    else:
        return {
            "game": f"{away} vs {home}",
            "pick": away,
            "edge": edge_away,
            "model": m_away,
            "market": p_away,
            "odds": away_o,
            "pitch": pitch,
            "stats": away_stats
        }


# =========================
# MAIN
# =========================

def main():

    log("START V5 QUANT PITCHER ENGINE")

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

        res = analyze(g, pitchers)
        if not res:
            continue

        if res["game"] in used:
            continue
        used.add(res["game"])

        s = res["stats"]

        msg = f"""🏦 MLB HEDGE FUND v5 (QUANT PITCHER ENGINE)

⚾ {res['game']}

🎯 PICK: {res['pick']}

📊 EDGE FINAL: {round(res['edge']*100,2)}%
📈 MODEL: {round(res['model']*100,2)}%
📉 MARKET: {round(res['market']*100,2)}%

💰 ODDS: {res['odds']}

🔥 PITCHER ENGINE:
- Away: {res['pitch']['away_name']}
- Home: {res['pitch']['home_name']}

📊 PITCHER STATS (IMPACT):
ERA: {s['era'] if s else 'N/A'}
WHIP: {s['whip'] if s else 'N/A'}
K/9: {s['k9'] if s else 'N/A'}

🧠 SYSTEM: TEAM + PITCHER WEIGHTED MODEL

────────────────────
"""

        send_message(msg)
        log(res["game"])


if __name__ == "__main__":
    main()
