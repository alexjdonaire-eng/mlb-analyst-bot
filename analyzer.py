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
# GET LATEST SNAPSHOTS
# =========================
def latest_games(history):
    games = {}

    for row in history:
        key = f"{row.get('away_team')}_{row.get('home_team')}"
        games.setdefault(key, []).append(row)

    return games


# =========================
# STEAM + CLV ANALYSIS
# =========================
def analyze_steam(game_snapshots):
    if len(game_snapshots) < 2:
        return None

    first = game_snapshots[0]
    last = game_snapshots[-1]

    odds_first = first.get("odds", {})
    odds_last = last.get("odds", {})

    if not odds_first or not odds_last:
        return None

    # comparar favorito inicial vs final
    first_fav = min(odds_first, key=odds_first.get)
    last_fav = min(odds_last, key=odds_last.get)

    steam_direction = "neutral"

    if first_fav == last_fav:
        steam_direction = "confirmed"
    else:
        steam_direction = "reverse"

    # CLV proxy: mejora o empeora precio
    first_price = odds_first[first_fav]
    last_price = odds_last.get(first_fav, first_price)

    clv = (first_price - last_price)  # positivo = mejoró

    return {
        "steam": steam_direction,
        "clv": clv,
        "fav": last_fav
    }


# =========================
# PICK SCORE (SHARP FILTER)
# =========================
def score_pick(prob, steam_data):
    score = 0

    # base probability
    if prob >= 62:
        score += 2
    elif prob >= 59:
        score += 1

    # steam logic
    if steam_data:
        if steam_data["steam"] == "confirmed":
            score += 2
        if steam_data["clv"] > 0:
            score += 2
        if steam_data["steam"] == "reverse":
            score -= 2

    return score


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

    for key, snaps in games.items():

        snaps = sorted(snaps, key=lambda x: x["time"])

        steam = analyze_steam(snaps)

        latest = snaps[-1]
        odds = latest.get("odds", {})

        if len(odds) < 2:
            continue

        winner = min(odds, key=odds.get)
        prob = (1 / odds[winner]) * 100

        score = score_pick(prob, steam)

        # 🔥 SHARP FILTER FINAL
        if score < 3:
            continue

        picks.append({
            "game": f"{latest.get('away_team')} vs {latest.get('home_team')}",
            "pick": winner,
            "prob": round(prob, 2),
            "steam": steam["steam"] if steam else "none",
            "clv": round(steam["clv"], 3) if steam else 0,
            "score": score
        })

    # ordenar por calidad real
    picks = sorted(picks, key=lambda x: x["score"], reverse=True)

    # =========================
    # REPORT
    # =========================
    report = "🏦 MLB STEAM + SHARP MONEY V8\n\n"

    for p in picks:
        report += (
            f"⚾ {p['game']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Prob: {p['prob']}%\n"
            f"🧠 Steam: {p['steam']}\n"
            f"📉 CLV: {p['clv']}\n"
            f"⭐ Score: {p['score']}\n"
            f"----------------------\n"
        )

    if len(picks) >= 2:
        report += "\n🔥 PARLEY STEAM\n\n"
        for p in picks[:4]:
            report += f"✔ {p['pick']} ({p['game']})\n"

    if was_sent(report):
        print("⚠️ DUPLICATE REPORT - SKIPPED")
        return

    send(report)
    mark_sent(report)

    print("✅ STEAM ANALYZER DONE")


if __name__ == "__main__":
    main()
