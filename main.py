import os
import requests
from datetime import datetime, timezone, timedelta

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

MLB_URL = "https://statsapi.mlb.com/api/v1/schedule"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

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
                "gameDate": g.get("gameDate"),
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_pitcher": g["teams"]["home"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "away_pitcher": g["teams"]["away"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "status": g.get("status", {}).get("detailedState", "")
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
# CALIBRATION
# =========================

def calibrate_prob(model_prob, market_prob):
    return (0.7 * market_prob) + (0.3 * model_prob)

# =========================
# EXPECTED VALUE
# =========================

def expected_value(prob, odds):
    payout = odds - 1
    return (prob * payout) - (1 - prob)

# =========================
# CORE EDGE ENGINE
# =========================

def get_edge(game):

    try:

        book = game["odds"]["bookmakers"][0]
        outs = book["markets"][0]["outcomes"]

        home = game["home_team"]
        away = game["away_team"]

        home_odds = None
        away_odds = None

        for o in outs:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            return None

        # MARKET PROBABILITY (vig removed)
        ph_mkt = 1 / home_odds
        pa_mkt = 1 / away_odds

        total = ph_mkt + pa_mkt
        ph_mkt /= total
        pa_mkt /= total

        # MODEL PROBABILITY (simple pitcher bias)
        ph_model = ph_mkt + 0.015 if game["home_pitcher"] != "UNKNOWN" else ph_mkt
        pa_model = pa_mkt

        # HOME SIDE
        if ph_model > pa_model:

            calibrated = calibrate_prob(ph_model, ph_mkt)
            ev = expected_value(calibrated, home_odds)
            edge = calibrated - ph_mkt

            return game["home_team"], edge, ev, calibrated

        # AWAY SIDE
        else:

            calibrated = calibrate_prob(pa_model, pa_mkt)
            ev = expected_value(calibrated, away_odds)
            edge = calibrated - pa_mkt

            return game["away_team"], edge, ev, calibrated

    except:
        return None

# =========================
# VALUE FILTER
# =========================

def is_value(edge, ev):

    if ev < 0:
        return False

    if edge < 0.015:
        return False

    return True

# =========================
# KELLY STAKE
# =========================

def kelly(edge):

    k = edge / 2

    if k < 0.01:
        return 0.01
    if k > 0.05:
        return 0.05

    return round(k, 3)

# =========================
# MAIN
# =========================

def main():

    print("🚀 V10.2 CALIBRATED EDGE SYSTEM")

    mlb = get_mlb_games()
    odds = get_odds()

    games = match_games(mlb, odds)

    bets = []

    for g in games:

        result = get_edge(g)
        if not result:
            continue

        pick, edge, ev, prob = result

        if not is_value(edge, ev):
            continue

        bets.append({
            "game": g,
            "pick": pick,
            "edge": edge,
            "ev": ev,
            "prob": prob,
            "stake": kelly(edge)
        })

    bets.sort(key=lambda x: x["ev"], reverse=True)

    report = "🏦 MLB V10.2 CALIBRATED EDGE SYSTEM\n\n"

    if not bets:
        report += "⚠️ No value bets today\n"

    for b in bets[:3]:

        g = b["game"]

        report += (
            f"🔥 TOP BET\n"
            f"⚾ {g['away_team']} vs {g['home_team']}\n"
            f"🎯 Pick: {b['pick']}\n"
            f"📊 Edge: {round(b['edge']*100,2)}%\n"
            f"💰 EV: {round(b['ev'],4)}\n"
            f"📈 Prob: {round(b['prob']*100,2)}%\n"
            f"💵 Stake: {round(b['stake']*100,1)}%\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ V10.2 SENT")

if __name__ == "__main__":
    main()
