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

def normalize(n):
    return n.lower().replace(" ", "")


# =========================
# RATINGS MODEL
# =========================

ratings = {
    "losangelesdodgers": 60,
    "newyorkyankees": 58,
    "atlantabraves": 57,
    "houstonastros": 56,
    "detroittigers": 55,
    "minnesotatwins": 54,
    "tampabayrays": 53,
    "seattlemariners": 52,
    "arizonadiamondbacks": 52,
    "sandiegopadres": 52,
    "texasrangers": 50,
    "cincinnatireds": 48,
    "losangelesangels": 47,
    "stlouiscardinals": 47,
    "miamimarlins": 45,
    "pittsburghpirates": 45,
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
    t = p1 + p2
    if t == 0:
        return 0, 0
    return p1 / t, p2 / t


# =========================
# PITCHERS (MLB + ESPN FUSION)
# =========================

def get_mlb_pitchers():

    url = MLB_URL + f"?sportId=1&date={datetime.utcnow().strftime('%Y-%m-%d')}&hydrate=probablePitcher"

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

            hp = g["teams"]["home"].get("probablePitcher")
            ap = g["teams"]["away"].get("probablePitcher")

            def name(p):
                return p.get("fullName") if p else "TBA"

            pitchers[(normalize(away), normalize(home))] = {
                "away_pitcher": name(ap),
                "home_pitcher": name(hp),
                "source": "MLB"
            }

    except:
        pass

    return pitchers


def get_espn_pitchers():

    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

    try:
        data = requests.get(url, timeout=10).json()
    except:
        return {}

    pitchers = {}

    for e in data.get("events", []):

        try:
            c = e["competitions"][0]["competitors"]

            home = away = None
            home_p = away_p = "TBA"

            for t in c:

                team = t["team"]["displayName"]

                prob = t.get("probables", [])

                p_name = "TBA"
                if prob:
                    p_name = prob[0].get("athlete", {}).get("displayName", "TBA")

                if t["homeAway"] == "home":
                    home = team
                    home_p = p_name
                else:
                    away = team
                    away_p = p_name

            if home and away:
                pitchers[(normalize(away), normalize(home))] = {
                    "away_pitcher": away_p,
                    "home_pitcher": home_p,
                    "source": "ESPN"
                }

        except:
            continue

    return pitchers


def merge_pitchers(mlb, espn):

    merged = mlb.copy()

    for k, v in espn.items():

        if k not in merged:
            merged[k] = v
            continue

        # ESPN override si MLB está incompleto
        if "TBA" in merged[k]["away_pitcher"] or "TBA" in merged[k]["home_pitcher"]:
            merged[k] = v

    return merged


def find_pitcher(pitchers, away, home):

    return pitchers.get(
        (normalize(away), normalize(home)),
        {"away_pitcher": "TBA", "home_pitcher": "TBA"}
    )


# =========================
# MODEL
# =========================

def model(home, away):

    h = ratings.get(normalize(home), 50)
    a = ratings.get(normalize(away), 50)

    diff = h - a

    p_home = 1 / (1 + (2.71828 ** (-diff / 10)))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# DATA QUALITY ENGINE
# =========================

def dq(game, pitch):

    score = 100

    if not game.get("bookmakers"):
        return 0

    if pitch["away_pitcher"] == "TBA":
        score -= 25
    if pitch["home_pitcher"] == "TBA":
        score -= 25

    return max(score, 0)


def conf(score):

    if score >= 80:
        return "🟢 FULL TRUST"
    if score >= 50:
        return "🟡 PARTIAL"
    return "🔴 BLOCK"


# =========================
# ANALYSIS
# =========================

def analyze(game, pitchers):

    home = game["home_team"]
    away = game["away_team"]

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

    pitch = find_pitcher(pitchers, away, home)

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

    log("🏦 HEDGE FUND v2 STARTED")

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

    mlb_p = get_mlb_pitchers()
    espn_p = get_espn_pitchers()

    pitchers = merge_pitchers(mlb_p, espn_p)

    results = []

    for g in games:

        if not g.get("bookmakers"):
            continue

        res = analyze(g, pitchers)

        if not res:
            continue

        score = dq(g, res["pitch"])

        if score < 50:
            continue

        results.append({
            **res,
            "dq": score
        })

    results.sort(key=lambda x: x["edge"], reverse=True)

    log(f"VALID PICKS: {len(results)}")

    for r in results[:5]:

        p = r["pitch"]

        msg = f"""🏦 MLB HEDGE FUND v2

{r['game']}

🎯 PICK: {r['pick']}
📊 EDGE: {round(r['edge']*100,2)}%
📈 MODEL: {round(r['model']*100,2)}%
📉 MARKET: {round(r['market']*100,2)}%

🔥 ODDS: {r['odds']}
🔥 PITCHERS: {p['away_pitcher']} vs {p['home_pitcher']}

🧪 DATA QUALITY: {r['dq']}/100 → {conf(r['dq'])}

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        send_message(msg)
        log(f"SENT {r['game']}")


if __name__ == "__main__":
    main()
