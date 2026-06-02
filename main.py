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

HISTORY_FILE = "market_history.jsonl"

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# =========================
# SAVE SNAPSHOT (WITH TIME LABEL)
# =========================

def save_snapshot(game_id, odds):

    hour = datetime.utcnow().hour

    if hour < 12:
        phase = "OPEN"
    elif hour < 18:
        phase = "MID"
    else:
        phase = "CLOSE"

    snapshot = {
        "time": datetime.utcnow().isoformat(),
        "game_id": game_id,
        "phase": phase,
        "odds": odds
    }

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

# =========================
# LOAD HISTORY
# =========================

def load_history(game_id):

    history = []

    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                obj = json.loads(line)

                if obj["game_id"] == game_id:
                    history.append(obj)

    except:
        pass

    return history

# =========================
# GET PHASE DATA
# =========================

def get_phase_data(history, phase):

    for h in history:
        if h.get("phase") == phase:
            return h["odds"]

    return None

# =========================
# STEAM (PHASE-BASED)
# =========================

def steam_phase(open_odds, close_odds, team):

    try:

        open_p = open_odds[team]
        close_p = close_odds[team]

        move = (open_p - close_p) / open_p

        if move > 0.03:
            return "SHARP STEAM"
        elif move > 0.015:
            return "MODERATE STEAM"

        return None

    except:
        return None

# =========================
# CLV REAL (OPEN → CLOSE)
# =========================

def clv_real(open_odds, close_odds, team):

    try:

        open_p = open_odds[team]
        close_p = close_odds[team]

        open_prob = 1 / open_p
        close_prob = 1 / close_p

        return close_prob - open_prob

    except:
        return 0

# =========================
# EDGE FINAL
# =========================

def edge_v117(model_prob, market_prob, clv):

    return (model_prob - market_prob) + (clv * 0.7)

# =========================
# GET ODDS
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
# ANALYZE GAME
# =========================

def analyze_game(game):

    try:

        book = game["bookmakers"][0]
        outs = book["markets"][0]["outcomes"]

        home = game["home_team"]
        away = game["away_team"]

        current = {
            home: None,
            away: None
        }

        for o in outs:
            current[o["name"]] = o["price"]

        save_snapshot(game["id"], current)

        history = load_history(game["id"])

        open_odds = get_phase_data(history, "OPEN")
        mid_odds = get_phase_data(history, "MID")
        close_odds = get_phase_data(history, "CLOSE")

        # fallback
        if not open_odds:
            open_odds = current
        if not close_odds:
            close_odds = current

        results = []

        for team in current.keys():

            # MARKET PROB
            market_prob = 1 / current[team]

            # SIMPLE MODEL (placeholder mejorable luego)
            model_prob = market_prob + 0.01

            clv = clv_real(open_odds, close_odds, team)
            steam = steam_phase(open_odds, close_odds, team)

            edge = edge_v117(model_prob, market_prob, clv)

            results.append({
                "game": game,
                "team": team,
                "edge": edge,
                "clv": clv,
                "steam": steam,
                "score": edge * 100
            })

        return results

    except:
        return None

# =========================
# MAIN
# =========================

def main():

    print("🚀 V11.7 TIME ENGINE FIX")

    odds = get_odds()

    all_results = []

    for game in odds:

        res = analyze_game(game)

        if not res:
            continue

        for r in res:
            all_results.append(r)

    all_results.sort(key=lambda x: x["score"], reverse=True)

    report = "🏦 MLB V11.7 TIME ENGINE\n\n"

    if not all_results:
        report += "⚠️ No market movement detected yet\n"

    for r in all_results[:3]:

        g = r["game"]

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
    print("✅ V11.7 SENT")

if __name__ == "__main__":
    main()
