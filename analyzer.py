import os
import requests
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SCORE = 8.0

# 📦 memoria simple de line movement (Railway runtime)
LAST_ODDS_FILE = "last_odds.json"


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


def implied_prob(odds):
    return (1 / odds) * 100


def load_last():
    try:
        with open(LAST_ODDS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_last(data):
    try:
        with open(LAST_ODDS_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass


def run(games):

    print("🧠 ANALYZER V3.5 LINE MOVEMENT START")

    last = load_last()
    current = {}

    report = "🏦 SHARP MONEY V3.5 LINE MOVEMENT\n\n"
    picks = 0

    for g in games:

        odds = g["odds"]

        if len(odds) < 2:
            continue

        team_a, team_b = list(odds.keys())

        oa = odds[team_a]
        ob = odds[team_b]

        # 📊 prob actual
        pa = implied_prob(oa)
        pb = implied_prob(ob)

        total = pa + pb
        pa = (pa / total) * 100
        pb = (pb / total) * 100

        # 🎯 pick base
        if pa > pb:
            pick = team_a
            base_score = pa - pb
        else:
            pick = team_b
            base_score = pb - pa

        # 📦 key del juego
        key = f"{g['home']}|{g['away']}"

        # 📈 LINE MOVEMENT DETECTION
        prev = last.get(key)

        movement_score = 0

        if prev:
            prev_a = prev["a"]
            prev_b = prev["b"]

            # movimiento hacia favorito/underdog
            movement_score = abs((pa - prev_a) + (pb - prev_b))

            # dirección del movimiento
            if (pa > prev_a and pick == team_a) or (pb > prev_b and pick == team_b):
                movement_score *= 1.2  # confirma sharp direction
            else:
                movement_score *= 0.8  # movimiento contra pick

        # 🧠 SCORE FINAL (sharp logic)
        score = base_score + (movement_score * 0.6)

        current[key] = {"a": pa, "b": pb}

        if score < MIN_SCORE:
            continue

        if score > 16:
            status = "🔥 STRONG SHARP (STEAM)"
        elif score > 11:
            status = "⚡ SHARP MOVE"
        else:
            status = "📊 VALUE MOVE"

        report += (
            f"⚾ {g['away']} vs {g['home']}\n"
            f"🎯 Pick: {pick}\n"
            f"📈 Score: {score:.2f}\n"
            f"📊 Movement: {movement_score:.2f}\n"
            f"🏷 Status: {status}\n\n"
            "----------------\n"
        )

        picks += 1

    save_last(current)

    if picks == 0:
        report += "⚠️ No sharp movement detected"

    send(report)

    print(f"✅ PICKS SENT: {picks}")

    return report
