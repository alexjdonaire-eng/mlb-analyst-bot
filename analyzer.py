import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SCORE = 9.0


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


def implied_prob(odds):
    return (1 / odds) * 100


# 🧠 normaliza mercado (reduce sesgo de cuotas extremas)
def normalize(a, b):
    total = a + b
    return (a / total) * 100, (b / total) * 100


def run(games):

    print("🏦 SHARP MONEY V4 INSTITUTIONAL REAL START")

    report = "🏦 SHARP MONEY V4 INSTITUTIONAL REAL\n\n"
    picks = 0

    for g in games:

        odds = g["odds"]

        if len(odds) < 2:
            continue

        teams = list(odds.keys())

        # 📊 prob implícita base
        probs = {t: implied_prob(o) for t, o in odds.items()}

        # 🔧 normalización de mercado
        vals = list(probs.values())
        norm_vals = normalize(vals[0], vals[1])

        probs[teams[0]] = norm_vals[0]
        probs[teams[1]] = norm_vals[1]

        # 🎯 favorito / underdog
        fav = max(probs, key=probs.get)
        dog = min(probs, key=probs.get)

        fav_score = probs[fav]
        dog_score = probs[dog]

        # 📈 edge base
        edge = abs(fav_score - dog_score)

        # 🧠 MARKET CONSENSUS SCORE (institucional clave)
        consensus = (fav_score + dog_score) / 2

        # 🧠 SHARP DISLOCATION (desbalance del mercado)
        dislocation = edge * (1 + abs(50 - consensus) / 50)

        # 🧠 FINAL SCORE (modelo institucional)
        score = (edge * 0.6) + (dislocation * 0.4)

        pick = fav if fav_score > dog_score else dog

        if score < MIN_SCORE:
            continue

        # 🧠 clasificación institucional
        if score > 18:
            status = "🔥 INSTITUTIONAL SHARP"
        elif score > 13:
            status = "⚡ SHARP MONEY"
        elif score > 10:
            status = "📊 CONSENSUS VALUE"
        else:
            status = "📈 EDGE"

        report += (
            f"⚾ {g['away']} vs {g['home']}\n"
            f"🎯 Pick: {pick}\n"
            f"📊 Score: {score:.2f}\n"
            f"📉 Edge: {edge:.2f}\n"
            f"🧠 Consensus: {consensus:.2f}\n"
            f"🏷 Status: {status}\n\n"
            "----------------\n"
        )

        picks += 1

    if picks == 0:
        report += "⚠️ No institutional edge detected (market efficient)"

    send(report)

    print(f"✅ PICKS SENT: {picks}")

    return report
