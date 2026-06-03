import os
import json
import requests
import hashlib

HISTORY_FILE = "market_history.jsonl"
MEM_FILE = "memory_store.json"
LAST_HASH_FILE = "last_send.hash"

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
# MEMORY (PERFORMANCE LEARNING)
# =========================
def load_memory():
    try:
        with open(MEM_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "wins": 0,
            "losses": 0,
            "prob_bins": {
                "55-60": {"w": 0, "l": 0},
                "60-70": {"w": 0, "l": 0}
            }
        }


def save_memory(mem):
    with open(MEM_FILE, "w") as f:
        json.dump(mem, f)


# =========================
# HISTORY
# =========================
def load_history():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                rows.append(json.loads(line))
    except:
        pass
    return rows


def latest_games(history):
    games = {}
    for r in history:
        key = f"{r.get('away_team')}_{r.get('home_team')}"
        games.setdefault(key, []).append(r)
    return games


# =========================
# CLV PROXY
# =========================
def clv_proxy(snaps):
    if len(snaps) < 2:
        return 0

    first = snaps[0]["odds"]
    last = snaps[-1]["odds"]

    try:
        f_team = min(first, key=first.get)
        l_team = min(last, key=last.get)

        if f_team != l_team:
            return -1  # reverse steam

        return first[f_team] - last.get(f_team, first[f_team])
    except:
        return 0


# =========================
# EV CALC
# =========================
def expected_value(prob, odds):
    decimal_odds = odds
    return (prob * decimal_odds) - 1


# =========================
# STAKING (SAFE KELLY)
# =========================
def staking(prob, odds):
    edge = (prob * odds) - 1

    if edge <= 0:
        return 0

    kelly = edge / odds

    # safety cap
    return round(min(kelly * 0.25, 0.05), 4)  # max 5% bankroll


# =========================
# HASH ANTI-SPAM
# =========================
def hash_report(text):
    return hashlib.md5(text.encode()).hexdigest()


def was_sent(report):
    try:
        with open(LAST_HASH_FILE, "r") as f:
            return f.read().strip() == hash_report(report)
    except:
        return False


def mark_sent(report):
    with open(LAST_HASH_FILE, "w") as f:
        f.write(hash_report(report))


# =========================
# MAIN
# =========================
def main():

    history = load_history()
    games = latest_games(history)
    mem = load_memory()

    picks = []

    for key, snaps in games.items():

        snaps = sorted(snaps, key=lambda x: x["time"])

        latest = snaps[-1]
        odds = latest.get("odds", {})

        if len(odds) < 2:
            continue

        team = min(odds, key=odds.get)
        price = odds[team]

        prob = (1 / price)

        ev = expected_value(prob, price)
        clv = clv_proxy(snaps)

        # FILTER INSTITUCIONAL
        if prob < 0.58:
            continue
        if ev < 0:
            continue

        stake = staking(prob, price)

        score = (prob * 100) + (clv * 10) + (ev * 100)

        picks.append({
            "game": f"{latest['away_team']} vs {latest['home_team']}",
            "pick": team,
            "prob": round(prob * 100, 2),
            "ev": round(ev, 3),
            "clv": round(clv, 3),
            "stake": stake,
            "score": round(score, 2)
        })

    picks = sorted(picks, key=lambda x: x["score"], reverse=True)

    # =========================
    # REPORT
    # =========================
    report = "🏦 V9 INSTITUTIONAL FUND MODEL\n\n"

    for p in picks:
        report += (
            f"⚾ {p['game']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Prob: {p['prob']}%\n"
            f"📉 EV: {p['ev']}\n"
            f"📈 CLV: {p['clv']}\n"
            f"💰 Stake: {p['stake'] * 100}% bankroll\n"
            f"⭐ Score: {p['score']}\n"
            f"----------------------\n"
        )

    if len(picks) >= 2:
        report += "\n🔥 PORTFOLIO\n\n"
        for p in picks[:4]:
            report += f"✔ {p['pick']} ({p['game']})\n"

    if was_sent(report):
        print("SKIP DUPLICATE")
        return

    send(report)
    mark_sent(report)

    print("V9 SENT")


if __name__ == "__main__":
    main()
