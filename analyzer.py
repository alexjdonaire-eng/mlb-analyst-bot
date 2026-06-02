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
        json={"chat_id": CHAT_ID, "text": msg},
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
# GROUP BY GAME
# =========================

def group_games(history):
    games = {}

    for row in history:
        gid = row.get("game_id")
        if not gid:
            continue

        if gid not in games:
            games[gid] = []
        games[gid].append(row)

    return games

# =========================
# GET FIRST AND LAST SNAPSHOT
# =========================

def get_movement(game_rows):
    if len(game_rows) < 2:
        return None

    first = game_rows[0]
    last = game_rows[-1]

    movement = []

    for team in first["odds"].keys():
        if team in last["odds"]:
            old = first["odds"][team]
            new = last["odds"][team]

            diff = round(new - old, 3)
            movement.append((team, old, new, diff))

    return movement

# =========================
# MAIN
# =========================

def main():

    history = load_history()
    games = group_games(history)

    report = "📈 MOVIMIENTO DE CUOTAS MLB\n\n"

    detected = 0

    for game_id, rows in games.items():

        movement = get_movement(rows)

        if not movement:
            continue

        away = rows[-1].get("away_team")
        home = rows[-1].get("home_team")

        text = f"⚾ {away} vs {home}\n\n"

        has_movement = False

        for team, old, new, diff in movement:

            if abs(diff) < 0.05:
                continue

            has_movement = True

            if diff < 0:
                direction = "📉 dinero entrando"
            else:
                direction = "📈 dinero saliendo"

            text += (
                f"{team}\n"
                f"{old} → {new}\n"
                f"{direction}\n\n"
            )

        if has_movement:
            report += text + "────────────────────\n\n"
            detected += 1

    if detected == 0:
        report = (
            "📈 MOVIMIENTO DE CUOTAS MLB\n\n"
            "⚠️ No hay movimientos significativos todavía."
        )

    send(report)
    print("✅ MOVEMENT ANALYZER SENT")


if __name__ == "__main__":
    main()
