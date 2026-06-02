import os
import json
import requests

HISTORY_FILE = "market_history.jsonl"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=20
    )


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


def group_games(history):
    games = {}
    for r in history:
        games.setdefault(r["game_id"], []).append(r)
    return games


def analyze_game(rows):

    rows.sort(key=lambda x: x["time"])

    if len(rows) < 3:
        return None

    signals = []

    # tomamos evolución por equipo
    teams = rows[0]["odds"].keys()

    for team in teams:

        prices = []

        for r in rows:
            if team in r["odds"]:
                prices.append(r["odds"][team])

        if len(prices) < 3:
            continue

        start = prices[0]
        end = prices[-1]

        change = end - start

        # volatilidad (movimiento total)
        volatility = max(prices) - min(prices)

        # sharp conditions
        if change < -0.15 and volatility > 0.20:
            signals.append((team, start, end, change, volatility))

    return signals


def main():

    history = load_history()
    games = group_games(history)

    report = "🔥 SHARP MONEY DETECTOR MLB\n\n"

    found = 0

    for gid, rows in games.items():

        signals = analyze_game(rows)

        if not signals:
            continue

        game = rows[-1]
        text = f"⚾ {game['away_team']} vs {game['home_team']}\n\n"

        for team, start, end, change, vol in signals:

            text += (
                f"🔥 {team}\n"
                f"{start} → {end}\n"
                f"Movimiento: {round(change, 3)}\n"
                f"Volatilidad: {round(vol, 3)}\n\n"
            )

        report += text + "────────────────────\n\n"
        found += 1

    if found == 0:
        report = "🔥 SHARP MONEY DETECTOR MLB\n\n⚠️ Sin movimientos institucionales detectados."

    send(report)
    print("SHARP ANALYZER SENT")


if __name__ == "__main__":
    main()
