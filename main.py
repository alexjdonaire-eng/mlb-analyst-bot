import os
import requests
from datetime import datetime, timezone, timedelta

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_URL = "https://statsapi.mlb.com/api/v1/schedule"


# =========================
# UTILIDADES
# =========================

def log(msg):
    print(f"[LOG] {msg}")


def send_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        log(e)


def normalize(x):
    return x.lower().replace(" ", "")


def now_caracas():
    utc = datetime.now(timezone.utc)
    caracas = utc - timedelta(hours=4)
    return caracas.strftime("%Y-%m-%d %H:%M")


# =========================
# PROBABILIDADES
# =========================

def prob(odds):
    return 1 / odds if odds else 0


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

    p_home = 1 / (1 + pow(2.71828, -diff / 10))
    p_away = 1 - p_home

    return p_home, p_away


# =========================
# PITCHERS (MLB + ESPN FUSION SAFE)
# =========================

def get_pitchers():

    pitchers = {}

    # --- MLB API ---
    try:
        url = MLB_URL + f"?sportId=1&date={datetime.utcnow().strftime('%Y-%m-%d')}&hydrate=probablePitcher"
        data = requests.get(url, timeout=10).json()

        games = data.get("dates", [])[0].get("games", [])

        for g in games:
            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            hp = g["teams"]["home"].get("probablePitcher")
            ap = g["teams"]["away"].get("probablePitcher")

            pitchers[(normalize(away), normalize(home))] = {
                "away": ap["fullName"] if ap else "TBA",
                "home": hp["fullName"] if hp else "TBA",
                "source": "MLB"
            }

    except:
        pass

    # --- ESPN fallback ---
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
        data = requests.get(url, timeout=10).json()

        for e in data.get("events", []):
            c = e["competitions"][0]["competitors"]

            home = away = None
            home_p = away_p = "TBA"

            for t in c:

                team = t["team"]["displayName"]
                prob = t.get("probables", [])

                pname = prob[0]["athlete"]["displayName"] if prob else "TBA"

                if t["homeAway"] == "home":
                    home = team
                    home_p = pname
                else:
                    away = team
                    away_p = pname

            if home and away:
                key = (normalize(away), normalize(home))

                if key not in pitchers or "TBA" in pitchers.get(key, {}).get("away", "TBA"):
                    pitchers[key] = {
                        "away": away_p,
                        "home": home_p,
                        "source": "ESPN"
                    }

    except:
        pass

    return pitchers


def get_pitch(pitchers, away, home):
    return pitchers.get(
        (normalize(away), normalize(home)),
        {"away": "TBA", "home": "TBA", "source": "NONE"}
    )


# =========================
# DATA QUALITY (SIMPLIFICADO)
# =========================

def dq(pitch):
    score = 100

    if pitch["away"] == "TBA":
        score -= 30
    if pitch["home"] == "TBA":
        score -= 30

    return max(score, 0)


def dq_label(score):

    if score >= 80:
        return "🟢 CONFIABLE"
    if score >= 50:
        return "🟡 PARCIAL"
    return "🔴 BAJA CONFIANZA"


# =========================
# ANALISIS
# =========================

def analyze(game, pitchers):

    home = game["home_team"]
    away = game["away_team"]

    book = game["bookmakers"][0]
    out = book["markets"][0]["outcomes"]

    home_o = away_o = None

    for o in out:
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

    print("🏦 MLB HEDGE FUND v3 STARTED")

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

        if not g.get("bookmakers"):
            continue

        res = analyze(g, pitchers)
        if not res:
            continue

        key = res["game"]
        if key in used:
            continue
        used.add(key)

        pitch = res["pitch"]

        dq_score = dq(pitch)

        if dq_score < 40:
            continue

        message = f"""🏦 MLB SHARP ALERT (HEDGE FUND v3)

⚾ Partido: {res['game']}

🎯 Pick del modelo: {res['pick']}

📊 Edge (ventaja real): {round(res['edge']*100,2)}%
📈 Modelo (probabilidad): {round(res['model']*100,2)}%
📉 Mercado (bookmaker): {round(res['market']*100,2)}%

💰 Cuota: {res['odds']}

🔥 Pitchers:
- Local: {pitch['away']}
- Visitante: {pitch['home']}
📡 Fuente: {pitch['source']}

🧠 Calidad del dato: {dq_score}/100 → {dq_label(dq_score)}

🕒 Hora Caracas: {now_caracas()}

────────────────────
"""

        send_message(message)
        print("sent:", res["game"])


if __name__ == "__main__":
    main()
