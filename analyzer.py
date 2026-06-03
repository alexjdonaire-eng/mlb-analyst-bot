import os
import json
import requests
import hashlib

HISTORY_FILE = "market_history.jsonl"
LAST_HASH_FILE = "last_send.hash"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
        print("✅ Telegram sent")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


# =========================
# HISTORY
# =========================
def load_history():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except:
                    continue
    except:
        pass
    return rows


# =========================
# LATEST SNAPSHOT PER GAME
# =========================
def latest_games(history):
    games = {}

    for row in reversed(history):
        key = f"{row.get('away_team')}_{row.get('home_team')}"
        if key not in games:
            games[key] = row

    return list(games.values())


# =========================
# PICK LOGIC
# =========================
def pick_winner(game):
    odds = game.get("odds", {})

    if len(odds) < 2:
        return None

    winner = min(odds, key=odds.get)
    prob = round((1 / odds[winner]) * 100, 2)

    return winner, prob


# =========================
# HASH ANTI-SPAM
# =========================
def make_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def was_sent(report):
    try:
        with open(LAST_HASH_FILE, "r") as f:
            return f.read().strip() == make_hash(report)
    except:
        return False


def mark_sent(report):
    with open(LAST_HASH_FILE, "w") as f:
        f.write(make_hash(report))


# =========================
# MAIN
# =========================
def main():

    history = load_history()
    games = latest_games(history)

    picks = []

    # =========================
    # BUILD PICKS (SIN LIMITE)
    # =========================
    for game in games:

        result = pick_winner(game)
        if not result:
            continue

        winner, prob = result

        if prob < 58:
            continue

        edge = prob - 50

        picks.append({
            "game": f"{game.get('away_team')} vs {game.get('home_team')}",
            "pick": winner,
            "prob": prob,
            "edge": edge
        })

    # ordenar por calidad
    picks = sorted(picks, key=lambda x: x["edge"], reverse=True)

    # =========================
    # REPORT
    # =========================
    report = "🏦 MLB PRO PARLEY CLEAN\n\n"

    for p in picks:
        report += (
            f"⚾ {p['game']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Prob: {p['prob']}%\n"
            f"📈 Edge: {p['edge']}%\n"
            f"----------------------\n"
        )

    # parley dinámico (mínimo 3 picks si existen)
    if len(picks) >= 3:
        report += "\n🔥 PARLEY DEL DÍA\n\n"
        for p in picks[:4]:
            report += f"✔ {p['pick']}\n"

    # =========================
    # ANTI-SPAM
    # =========================
    if was_sent(report):
        print("⚠️ DUPLICATE REPORT - SKIPPED")
        return

    send(report)
    mark_sent(report)

    print("✅ ANALYZER DONE")


if __name__ == "__main__":
    main()
