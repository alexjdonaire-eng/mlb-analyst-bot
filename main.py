import os
import json
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
# SNAPSHOT STORAGE
# =========================

def save_snapshot(game_id, data):

    snapshot = {
        "time": datetime.utcnow().isoformat(),
        "game_id": game_id,
        "data": data
    }

    with open("odds_history.jsonl", "a") as f:
        f.write(json.dumps(snapshot) + "\n")

# =========================
# LOAD HISTORY
# =========================

def load_history(game_id):

    try:
        with open("odds_history.jsonl", "r") as f:
            lines = f.readlines()

        history = []

        for l in lines:
            obj = json.loads(l)

            if obj["game_id"] == game_id:
                history.append(obj)

        return history

    except:
        return []

# =========================
# CURRENT ODDS
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
# STEAM DETECTION (REAL)
# =========================

def steam_signal(open_line, current_line, team):

    if not open_line or not current_line:
        return None

    try:

        open_price = open_line["data"][team]
        current_price = current_line[team]

        move = (open_price - current_price) / open_price

        if move > 0.03:
            return "SHARP STEAM"
        elif move > 0.015:
            return "MODERATE STEAM"

        return None

    except:
        return None

# =========================
# CLV REAL
# =========================

def clv(open_line, current_line, team):

    try:

        open_price = open_line["data"][team]
        current_price = current_line[team]

        return (current_price - open_price) / open_price

    except:
        return 0

# =========================
# EDGE FINAL
# =========================

def final_edge(model_prob, market_prob, clv_value):

    base = model_prob - market_prob
    return base + (clv_value * 0.5)

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
# ANALYZE GAME
# =========================

def analyze_game(game):

    try:

        book = game["bookmakers"][0]
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

        # MARKET PROB
        ph_mkt = 1 / home_odds
        pa_mkt = 1 / away_odds

        total = ph_mkt + pa_mkt
        ph_mkt /= total
        pa_mkt /= total

        # SIMPLE MODEL
        ph_model = ph_mkt + 0.015
        pa_model = pa_mkt

        history = load_history(game["id"])
        open_line = history[0] if history else None

        current = {
            home: home_odds,
            away: away_odds
        }

        results = []

        for team in current.keys():

            steam = steam_signal(open_line, current, team)
            clv_value = clv(open_line, current, team)

            market_prob = 1 / current[team]
            model_prob = market_prob + (0.01 if team == home else 0)

            edge = final_edge(model_prob, market_prob, clv_value)

            results.append({
                "team": team,
                "edge": edge,
                "clv": clv_value,
                "steam": steam,
                "score": edge * 100
            })

        return game, results

    except:
        return None

# =========================
# MAIN
# =========================

def main():

    print("🚀 V11.5 MARKET DATA LAYER")

    odds = get_odds()

    all_results = []

    for game in odds:

        result = analyze_game(game)

        if not result:
            continue

        g, res = result

        # save snapshot (OPEN-LIKE STATE)
        try:
            save_snapshot(g["id"], {
                g["home_team"]: 1 / res[0]["edge"] if res else 1,
                g["away_team"]: 1 / res[1]["edge"] if len(res) > 1 else 1
            })
        except:
            pass

        for r in res:
            all_results.append((g, r))

    all_results.sort(key=lambda x: x[1]["score"], reverse=True)

    report = "🏦 MLB V11.5 MARKET INTELLIGENCE\n\n"

    if not all_results:
        report += "⚠️ No market inefficiencies detected\n"

    for g, r in all_results[:3]:

        report += (
            f"🔥 SHARP SIGNAL\n"
            f"⚾ {g['away_team']} vs {g['home_team']}\n"
            f"🎯 Pick: {r['team']}\n"
            f"📊 Edge: {round(r['edge']*100,2)}%\n"
            f"📈 CLV: {round(r['clv']*100,2)}%\n"
            f"🔥 Steam: {r['steam']}\n"
            f"⭐ Score: {round(r['score'],2)}\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ V11.5 SENT")

if __name__ == "__main__":
    main()
