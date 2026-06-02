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

    picks = []

    for game in games:

        result = pick_winner(game)

        if not result:
            continue

        winner, prob = result

        picks.append({
            "game": game,
            "winner": winner,
            "prob": prob
        })

    picks.sort(key=lambda x: x["prob"], reverse=True)

    report = "🔥 TOP 3 PICKS DEL DÍA\n\n"

    for i, pick in enumerate(picks[:3], start=1):
        report += (
            f"{i}️⃣ {pick['winner']} ({pick['prob']}%)\n"
        )

    report += "\n━━━━━━━━━━━━━━━━\n\n"
    report += "🏦 MLB PREDICCIONES\n\n"

    total = 0

    for pick in picks:

        game = pick["game"]

        away = game.get("away_team")
        home = game.get("home_team")

        winner = pick["winner"]
        prob = pick["prob"]

        if prob >= 65:
            confidence = "🔥 ALTA"
        elif prob >= 58:
            confidence = "✅ MEDIA"
        else:
            confidence = "⚠️ BAJA"

        report += (
            f"⚾ {away} vs {home}\n\n"
            f"🎯 Ganador: {winner} ({prob}%)\n"
            f"📊 Confianza: {confidence}\n"
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
