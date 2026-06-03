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
                    continue
    except:
        pass
    return rows


# =========================
# GET LATEST GAMES
# =========================
def latest_games(history):
    games = {}

    for row in reversed(history):
        key = f"{row.get('away_team')}_{row.get('home_team')}"
        if key not in games:
            games[key] = row

    return list(games.values())


# =========================
# PICK MODEL (PRE-GAME FILTERED)
# =========================
def pick_winner(game):
    odds = game.get("odds", {})

    if len(odds) < 2:
        return None

    winner = min(odds, key=odds.get)
    prob = (1 / odds[winner]) * 100

    return winner, prob


# =========================
# ANTI-SPAM HASH
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
    # FILTER PRE-GAME (CLAVE)
    # =========================
    for game in games:

        result = pick_winner(game)
        if not result:
            continue

        winner, prob = result

        # 🔥 FILTRO MÁS ESTRICTO (menos ruido)
        if prob < 59:
            continue

        edge = prob - 50

        # solo picks realmente “jugables”
        if edge < 9:
            continue

        picks.append({
            "game": f"{game.get('away_team')} vs {game.get('home_team')}",
            "pick": winner,
            "prob": round(prob, 2),
            "edge": round(edge, 2)
        })

    # ordenar calidad real
    picks = sorted(picks, key=lambda x: x["edge"], reverse=True)

    # =========================
    # REPORT
    # =========================
    report = "🏦 MLB PRE-GAME FINAL\n\n"

    for p in picks:
        report += (
            f"⚾ {p['game']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Prob: {p['prob']}%\n"
            f"📈 Edge: {p['edge']}%\n"
            f"----------------------\n"
        )

    # =========================
    # PARLEY ESTABLE (2–4 PICKS)
    # =========================
    if len(picks) >= 2:
        report += "\n🔥 PARLEY PRE-GAME\n\n"

        for p in picks[:4]:
            report += f"✔ {p['pick']} ({p['game']})\n"

    else:
        report += "\n⚠️ Sin parley estable hoy (poca edge quality)\n"

    # =========================
    # ANTI-SPAM FINAL
    # =========================
    if was_sent(report):
        print("⚠️ DUPLICATE REPORT - SKIPPED")
        return

    send(report)
    mark_sent(report)

    print("✅ PRE-GAME ANALYZER DONE")


if __name__ == "__main__":
    main()
