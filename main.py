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
# EDGE CALC
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

        ph = 1 / home_odds
        pa = 1 / away_odds

        total = ph + pa
        ph /= total
        pa /= total

        # ajuste pitcher simple
        if game["home_pitcher"] != "UNKNOWN":
            ph += 0.01

        if ph > pa:
            return game["home_team"], ph - pa, ph, pa
        else:
            return game["away_team"], pa - ph, pa, ph

    except:
        return None

# =========================
# SCORING SYSTEM
# =========================

def calculate_score(edge, confidence, stability, risk):
    return (edge * 100) + confidence + stability - risk

# =========================
# KELLY STAKE
# =========================

def kelly(edge):

    if edge <= 0:
        return 0.01

    k = edge / 2

    if k < 0.01:
        return 0.01
    if k > 0.05:
        return 0.05

    return round(k, 3)

# =========================
# BUILD BETS
# =========================

def build_bets(raw):

    bets = []

    for r in raw:

        edge = r["edge"]

        score = calculate_score(
            edge,
            r.get("confidence", 55),
            r.get("stability", 50),
            r.get("risk", 20)
        )

        bets.append({
            "game": r["game"],
            "pick": r["pick"],
            "edge": edge,
            "score": score,
            "stake": kelly(edge),
            "home_prob": r["home_prob"],
            "away_prob": r["away_prob"]
        })

    return bets

# =========================
# RANKING
# =========================

def rank_bets(bets):
    return sorted(bets, key=lambda x: x["score"], reverse=True)

# =========================
# OUTPUT
# =========================

def build_report(bets):

    report = "🏦 MLB V10 AUTO BET RANKING\n\n"

    top = bets[:3]

    for i, b in enumerate(top, 1):

        g = b["game"]

        risk = "🟢 LOW" if b["stake"] <= 0.02 else "🟡 MEDIUM" if b["stake"] <= 0.04 else "🔴 HIGH"

        report += (
            f"🔥 TOP {i}\n"
            f"⚾ {g['away_team']} vs {g['home_team']}\n"
            f"🎯 Pick: {b['pick']}\n"
            f"📊 Edge: {round(b['edge']*100,2)}%\n"
            f"⭐ Score: {round(b['score'],2)}\n"
            f"💰 Stake: {round(b['stake']*100,1)}%\n"
            f"⚠️ Risk: {risk}\n\n"
            f"────────────────────\n\n"
        )

    return report

# =========================
# MAIN
# =========================

def main():

    print("🚀 V10 AUTO BET RANKING SYSTEM")

    mlb = get_mlb_games()
    odds = get_odds()

    games = match_games(mlb, odds)

    raw_bets = []

    for g in games:

        result = get_edge(g)
        if not result:
            continue

        pick, edge, home_p, away_p = result

        raw_bets.append({
            "game": g,
            "pick": pick,
            "edge": edge,
            "home_prob": home_p,
            "away_prob": away_p,
            "confidence": 55,
            "stability": 50,
            "risk": 20
        })

    bets = build_bets(raw_bets)

    ranked = rank_bets(bets)

    report = build_report(ranked)

    send(report)
    print("✅ V10 SENT")

if __name__ == "__main__":
    main()
