import json
import os
import requests

HISTORY_FILE = "market_history.jsonl"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# CONFIG PRO
# =========================
MIN_PROB = 63.0
MIN_EDGE = 10.0
MAX_PICKS = 3

seen = set()

# =========================
def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=20
    )

# =========================
def load_history():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    except:
        pass
    return rows

# =========================
def latest_games(history):
    games = {}
    for row in reversed(history):
        key = f"{row.get('away_team')}_{row.get('home_team')}"
        if key not in games:
            games[key] = row
    return list(games.values())

# =========================
def pick(game):
    odds = game.get("odds", {})
    if len(odds) < 2:
        return None

    winner = min(odds, key=odds.get)
    prob = round((1 / odds[winner]) * 100, 2)
    edge = round(prob - 50, 2)

    return winner, prob, edge

# =========================
def main():
    history = load_history()
    games = latest_games(history)

    picks = []

    for game in games:
        away = game.get("away_team")
        home = game.get("home_team")

        result = pick(game)
        if not result:
            continue

        winner, prob, edge = result

        key = f"{away}_{home}_{winner}"
        if key in seen:
            continue

        if prob < MIN_PROB:
            continue

        if edge < MIN_EDGE:
            continue

        seen.add(key)

        picks.append(
            f"""⚾ {away} vs {home}
🎯 Pick: {winner}
📊 Prob: {prob}%
📈 Edge: {edge}%
"""
        )

        if len(picks) >= MAX_PICKS:
            break

    if not picks:
        print("NO VALUE PICKS")
        return

    msg = "🏦 MLB PRO BETTING BOT V2\n\n" + "\n----------------\n".join(picks)

    send(msg)
    print("SENT PICKS:", len(picks))

if __name__ == "__main__":
    main()
