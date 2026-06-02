import os
import json
import requests

HISTORY_FILE = "market_history.jsonl"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM
# =========================

def send(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# =========================
# LOAD HISTORY
# =========================

def load_history():

    data = []

    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                data.append(json.loads(line))
    except:
        pass

    return data

# =========================
# GROUP BY GAME
# =========================

def group_by_game(history):

    games = {}

    for h in history:

        gid = h["game_id"]

        if gid not in games:
            games[gid] = []

        games[gid].append(h)

    return games

# =========================
# CLV
# =========================

def clv(open_odds, close_odds, team):

    try:
        return (1 / close_odds[team]) - (1 / open_odds[team])
    except:
        return 0

# =========================
# STEAM
# =========================

def steam(open_odds, close_odds, team):

    try:

        move = (open_odds[team] - close_odds[team]) / open_odds[team]

        if move > 0.03:
            return "SHARP STEAM"
        elif move > 0.015:
            return "MODERATE STEAM"

        return None

    except:
        return None

# =========================
# ANALYZE GAME
# =========================

def analyze_game(history):

    if len(history) < 2:
        return None

    open_odds = history[0]["odds"]
    close_odds = history[-1]["odds"]

    results = []

    for team in close_odds.keys():

        market_prob = 1 / close_odds[team]
        model_prob = market_prob + 0.01

        edge = model_prob - market_prob
        clv_val = clv(open_odds, close_odds, team)
        steam_val = steam(open_odds, close_odds, team)

        results.append({
            "team": team,
            "edge": edge,
            "clv": clv_val,
            "steam": steam_val,
            "score": (edge + clv_val) * 100
        })

    return results

# =========================
# MAIN
# =========================

def main():

    history = load_history()
    games = group_by_game(history)

    all_results = []

    for gid, h in games.items():

        res = analyze_game(h)

        if not res:
            continue

        for r in res:
            all_results.append((gid, r))

    all_results.sort(key=lambda x: x[1]["score"], reverse=True)

    report = "🏦 MLB ANALYZER V11.9\n\n"

    if not all_results:
        report += "⚠️ No data yet. Espera más snapshots.\n"

    for gid, r in all_results[:5]:

        report += (
            f"🔥 SHARP SIGNAL\n"
            f"🎯 Pick: {r['team']}\n"
            f"📊 Edge: {round(r['edge']*100,2)}%\n"
            f"📈 CLV: {round(r['clv']*100,2)}%\n"
            f"🔥 Steam: {r['steam']}\n"
            f"⭐ Score: {round(r['score'],2)}\n\n"
            f"────────────────────\n\n"
        )

    send(report)
    print("✅ ANALYZER SENT")

if __name__ == "__main__":
    main()
