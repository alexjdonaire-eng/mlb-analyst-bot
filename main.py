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
# MATCHING (NO DUPLICATES)
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

        # pequeño ajuste pitcher
        if game["home_pitcher"] != "UNKNOWN":
            ph += 0.01

        if ph > pa:
            return game["home_team"], ph - pa
        else:
            return game["away_team"], pa - ph

    except:
        return None

# =========================
# FILTER (BETTING WINDOW + LIVE)
# =========================

def classify(game):

    try:

        t = datetime.fromisoformat(game["gameDate"].replace("Z", "+00:00")).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)

        window_start = now - timedelta(hours=3)
        window_end = now + timedelta(hours=18)

        status = game.get("status", "").lower()

        if "final" in status:
            return None

        if "in progress" in status:
            return "LIVE"

        if t < window_start or t > window_end:
            return None

        return "PRE"

    except:
        return None

# =========================
# MAIN
# =========================

def main():

    print("🚀 V8.1 CLEAN EDGE SYSTEM")

    mlb = get_mlb_games()
    odds = get_odds()

    games = match_games(mlb, odds)

    picks = []

    for g in games:

        state = classify(g)
        if not state:
            continue

        result = get_edge(g)
        if not result:
            continue

        pick, edge = result

        # filtro de valor real
        if edge < 0.03:
            continue

        picks.append({
            "game": g,
            "pick": pick,
            "edge": edge,
            "state": state
        })

    picks.sort(key=lambda x: x["edge"], reverse=True)

    report = "🏦 MLB V8.1 CLEAN EDGE\n\n"

    for p in picks[:5]:

        g = p["game"]

        report += (
            f"{'🔴' if p['state']=='LIVE' else '🟢'} {g['away_team']} vs {g['home_team']}\n"
            f"🏟 {g['away_pitcher']} vs {g['home_pitcher']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Edge: {round(p['edge']*100,2)}%\n\n"
            f"────────────────────\n\n"
        )

    if not picks:
        report += "⚠️ No value bets found today."

    send(report)
    print("✅ DONE")

if __name__ == "__main__":
    main()
