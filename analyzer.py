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
        json={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=20
    )

# =========================
# LOAD HISTORY
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
# LATEST GAME SNAPSHOTS
# =========================

def latest_games(history):

    games = {}

    for row in reversed(history):

        away = row.get("away_team")
        home = row.get("home_team")

        if not away or not home:
            continue

        key = f"{away}_{home}"

        if key not in games:
            games[key] = row

    return list(games.values())

# =========================
# PICK WINNER
# =========================

def pick_winner(game):

    odds = game.get("odds", {})

    if len(odds) < 2:
        return None

    winner = min(odds, key=odds.get)

    prob = round((1 / odds[winner]) * 100, 1)

    return winner, prob

# =========================
# MAIN
# =========================

def main():

    history = load_history()

    games = list(latest_games(history))

    print("TOTAL GAMES:", len(games))

    for g in games:
        print(
            g.get("away_team"),
            "vs",
            g.get("home_team"),
            "|",
            g.get("game_id")
        )

    report = "🏦 MLB PREDICCIONES\n\n"

    total = 0

    for game in games:

        away = game.get("away_team")
        home = game.get("home_team")

        result = pick_winner(game)

        if not away or not home or not result:
            continue

        winner, prob = result

        report += (
            f"⚾ {away} vs {home}\n\n"
            f"🎯 Ganador: {winner} ({prob}%)\n"
            f"⭐ Mejor jugada: {winner}\n\n"
            f"────────────────────\n\n"
        )

        total += 1

    if total == 0:

        report = (
            "🏦 MLB PREDICCIONES\n\n"
            "⚠️ No hay suficientes datos todavía.\n"
            "Espera algunos snapshots más."
        )

    send(report)

    print("✅ ANALYZER SENT")

if __name__ == "__main__":
    main()
