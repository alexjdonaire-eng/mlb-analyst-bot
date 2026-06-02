import os
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MLB_URL = "https://statsapi.mlb.com/api/v1/schedule"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# =========================
# NORMALIZER
# =========================

def normalize(name):
    return (
        name.lower()
        .replace("new york", "ny")
        .replace("los angeles", "la")
        .replace("st. louis", "st louis")
        .replace(" ", "")
    )

# =========================
# MLB DATA
# =========================

def get_mlb_games():

    today = datetime.now().strftime("%Y-%m-%d")

    url = f"{MLB_URL}?sportId=1&date={today}&hydrate=probablePitcher"
    r = requests.get(url)

    if r.status_code != 200:
        return []

    data = r.json()
    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            games.append({
                "id": g.get("gamePk"),
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_pitcher": g["teams"]["home"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "away_pitcher": g["teams"]["away"].get("probablePitcher", {}).get("fullName") or "UNKNOWN"
            })

    return games

# =========================
# ODDS DATA
# =========================

def get_odds():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    return r.json() if r.status_code == 200 else []

# =========================
# MATCHING
# =========================

def match_games(mlb, odds):

    matched = []
    used = set()

    for m in mlb:

        mh = normalize(m["home_team"])
        ma = normalize(m["away_team"])
        key = f"{mh}_vs_{ma}"

        for o in odds:

            oh = normalize(o["home_team"])
            oa = normalize(o["away_team"])

            k1 = f"{oh}_vs_{oa}"
            k2 = f"{oa}_vs_{oh}"

            if (key == k1 or key == k2) and key not in used:

                matched.append({**m, "odds": o})
                used.add(key)
                break

    return matched

# =========================
# STEAM DETECTION
# =========================

def steam_signal(open_price, current_price):

    if not open_price:
        return None

    move = (open_price - current_price) / open_price

    if move > 0.03:
        return "SHARP EARLY MOVE"
    elif move > 0.015:
        return "MODERATE STEAM"

    return None

# =========================
# MARKET BIAS
# =========================

def market_bias(model_prob, market_prob):

    diff = model_prob - market_prob

    if diff > 0.04:
        return "UNDERVALUED TEAM"
    elif diff < -0.04:
        return "OVERVALUED TEAM"

    return None

# =========================
# CLV FORECAST
# =========================

def projected_clv(model_prob, market_prob, steam):

    base = model_prob - market_prob

    if steam == "SHARP EARLY MOVE":
        base += 0.02
    elif steam == "MODERATE STEAM":
        base += 0.01

    return base

# =========================
# EDGE V11
# =========================

def v11_edge(model_prob, market_prob, steam):

    clv = projected_clv(model_prob, market_prob, steam)

    if clv < 0.01:
        return None

    return clv

# =========================
# CORE ANALYSIS
# =========================

def analyze_game(game, model_prob, market_prob, open_price, current_price):

    steam = steam_signal(open_price, current_price)
    bias = market_bias(model_prob, market_prob)
    edge = v11_edge(model_prob, market_prob, steam)

    if not edge:
        return None

    score = edge * 100

    return {
        "game": game,
        "edge": edge,
        "score": score,
        "steam": steam,
        "bias": bias
    }

# =========================
# MAIN MODEL (SIMPLE PROB MODEL)
# =========================

def simple_model(game):

    # modelo base simple (puedes mejorar luego con pitchers reales)
    return 0.52, 0.48

# =========================
# MAIN
# =========================

def main():

    print("🚀 V11 SHARP INTELLIGENCE SYSTEM")

    mlb = get_mlb_games()
    odds = get_odds()

    games = match_games(mlb, odds)

    results = []

    for g in games:

        try:
            book = g["odds"]["bookmakers"][0]
            outs = book["markets"][0]["outcomes"]

            home = g["home_team"]
            away = g["away_team"]

            home_odds = None
            away_odds = None

            for o in outs:
                if o["name"] == home:
                    home_odds = o["price"]
                if o["name"] == away:
                    away_odds = o["price"]

            if not home_odds or not away_odds:
                continue

            ph_mkt = 1 / home_odds
            pa_mkt = 1 / away_odds

            total = ph_mkt + pa_mkt
            ph_mkt /= total
            pa_mkt /= total

            # simple model
            ph_model, pa_model = simple_model(g)

            # home side
            result_home = analyze_game(g, ph_model, ph_mkt, home_odds, home_odds)

            # away side
            result_away = analyze_game(g, pa_model, pa_mkt, away_odds, away_odds)

            if result_home:
                results.append(result_home)

            if result_away:
                results.append(result_away)

        except:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)

    report = "🏦 MLB V11 SHARP INTELLIGENCE\n\n"

    if not results:
        report += "⚠️ No early market inefficiencies detected today\n"

    for r in results[:3]:

        g = r["game"]

        report += (
            f"🔥 SHARP SIGNAL\n"
            f"⚾ {g['away_team']} vs {g['home_team']}\n"
            f"🎯 Edge: {round(r['edge']*100,2)}%\n"
            f"📈 Score: {round(r['score'],2)}\n"
            f"🔥 Steam: {r['steam']}\n"
            f"⚠️ Bias: {r['bias']}\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ V11 SENT")

if __name__ == "__main__":
    main()
