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
# SAVE SNAPSHOT (TIME SERIES)
# =========================

def save_snapshot(game_id, odds):

    snapshot = {
        "time": datetime.utcnow().isoformat(),
        "game_id": game_id,
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
# STEAM VELOCITY
# =========================

def steam_velocity(history, team):

    if len(history) < 2:
        return 0

    try:

        first = history[0]["odds"][team]
        last = history[-1]["odds"][team]

        move = (first - last) / first

        speed = move / len(history)

        return speed

    except:
        return 0

# =========================
# CLV CURVE
# =========================

def clv_curve(history, team):

    values = []

    try:

        for h in history:
            odds = h["odds"][team]
            prob = 1 / odds
            values.append(prob)

        if len(values) < 2:
            return 0

        return values[-1] - values[0]

    except:
        return 0

# =========================
# SHARP SIGNAL
# =========================

def sharp_signal(speed, clv):

    if speed > 0.02 and clv > 0.01:
        return "SHARP MONEY CONFIRMED"

    if speed > 0.01:
        return "MODERATE STEAM"

    return None

# =========================
# EDGE V11.6
# =========================

def edge_v116(model_prob, market_prob, clv):

    return (model_prob - market_prob) + (clv * 0.6)

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

        home_odds = None
        away_odds = None

        for o in outs:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            return None

        current_odds = {
            home: home_odds,
            away: away_odds
        }

        # SAVE SNAPSHOT (for time series)
        save_snapshot(game["id"], current_odds)

        history = load_history(game["id"])

        if not history:
            return None

        latest = history[-1]["odds"]

        results = []

        for team in latest.keys():

            speed = steam_velocity(history, team)
            clv = clv_curve(history, team)
            signal = sharp_signal(speed, clv)

            market_prob = 1 / latest[team]
            model_prob = market_prob + (0.01 if team == home else 0)

            edge = edge_v116(model_prob, market_prob, clv)

            results.append({
                "game": game,
                "team": team,
                "edge": edge,
                "speed": speed,
                "clv": clv,
                "signal": signal,
                "score": edge * 100
            })

        return results

    except:
        return None

# =========================
# MAIN
# =========================

def main():

    print("🚀 V11.6 MARKET TIME WINDOW ENGINE")

    odds = get_odds()

    all_results = []

    for game in odds:

        result = analyze_game(game)

        if not result:
            continue

        for r in result:
            all_results.append(r)

    all_results.sort(key=lambda x: x["score"], reverse=True)

    report = "🏦 MLB V11.6 MARKET INTELLIGENCE\n\n"

    if not all_results:
        report += "⚠️ No market movement detected\n"

    for r in all_results[:3]:

        g = r["game"]

        report += (
            f"🔥 SHARP SIGNAL\n"
            f"⚾ {g['away_team']} vs {g['home_team']}\n"
            f"🎯 Pick: {r['team']}\n"
            f"📊 Edge: {round(r['edge']*100,2)}%\n"
            f"📈 CLV Curve: {round(r['clv']*100,2)}%\n"
            f"⚡ Steam Speed: {round(r['speed'],4)}\n"
            f"🔥 Signal: {r['signal']}\n"
            f"⭐ Score: {round(r['score'],2)}\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ V11.6 SENT")

if __name__ == "__main__":
    main()
