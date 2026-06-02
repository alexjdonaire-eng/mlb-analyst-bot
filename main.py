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

def normalize_team(name):
    return (
        name.lower()
        .replace("new york", "ny")
        .replace("los angeles", "la")
        .replace("st. louis", "st louis")
        .replace(" ", "")
    )

# =========================
# MLB
# =========================

def get_mlb_games():

    today = datetime.now().strftime("%Y-%m-%d")

    url = f"{MLB_URL}?sportId=1&date={today}&hydrate=probablePitcher"
    r = requests.get(url)

    if r.status_code != 200:
        return []

    data = r.json()
    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):

            games.append({
                "id": game.get("gamePk"),
                "gameDate": game.get("gameDate"),
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "away_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "status": game.get("status", {}).get("detailedState", "")
            })

    return games

# =========================
# ODDS
# =========================

def get_odds_games():

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

def match_games(mlb_games, odds_games):

    matched = []
    used = set()

    for m in mlb_games:

        mh = normalize_team(m["home_team"])
        ma = normalize_team(m["away_team"])
        key = f"{mh}_vs_{ma}"

        for o in odds_games:

            oh = normalize_team(o["home_team"])
            oa = normalize_team(o["away_team"])
            okey1 = f"{oh}_vs_{oa}"
            okey2 = f"{oa}_vs_{oh}"

            if (key == okey1 or key == okey2) and key not in used:

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
        outcomes = book["markets"][0]["outcomes"]

        home = game["home_team"]
        away = game["away_team"]

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            return None

        # implied probability
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds

        # normalize
        total = home_prob + away_prob
        home_prob /= total
        away_prob /= total

        # simple model bias (pitcher placeholder)
        bias = 0.02 if game["home_pitcher"] != "UNKNOWN" else 0

        home_prob += bias

        if home_prob > away_prob:
            edge = home_prob - away_prob
            return game["home_team"], edge
        else:
            edge = away_prob - home_prob
            return game["away_team"], edge

    except:
        return None

# =========================
# FILTER (REAL BETTING WINDOW)
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

    print("🚀 V8.1 EDGE SYSTEM")

    mlb = get_mlb_games()
    odds = get_odds_games()

    games = match_games(mlb, odds)

    picks = []

    live = 0
    pre = 0

    for g in games:

        state = classify(g)
        if not state:
            continue

        result = get_edge(g)
        if not result:
            continue

        pick, edge = result

        if edge < 0.03:  # 🔥 FILTRO VALUE REAL
            continue

        picks.append({
            "game": g,
            "pick": pick,
            "edge": edge,
            "state": state
        })

    # ordenar por mejor edge
    picks.sort(key=lambda x: x["edge"], reverse=True)

    report = "🏦 MLB V8.1 EDGE SYSTEM\n\n"

    for p in picks[:8]:

        g = p["game"]

        report += (
            f"{'🔴' if p['state']=='LIVE' else '🟢'} {g['away_team']} vs {g['home_team']}\n"
            f"🏟 {g['away_pitcher']} vs {g['home_pitcher']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Edge: {round(p['edge']*100,2)}%\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ Sent")

if __name__ == "__main__":
    main()
