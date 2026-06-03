import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SCORE = 7.5  # más estricto = más precisión

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )

def implied_prob(odds):
    return (1 / odds) * 100


# 🔥 elimina sesgo del mercado (normalización simple)
def normalize_probs(p1, p2):
    total = p1 + p2
    return (p1 / total) * 100, (p2 / total) * 100


def run(games):

    print("🧠 ANALYZER V2.1 START")

    report = "🏦 SHARP MONEY ANALYZER V2.1\n\n"
    picks = 0

    for g in games:

        odds = g["odds"]

        if len(odds) < 2:
            continue

        team_a, team_b = list(odds.keys())

        oa = odds[team_a]
        ob = odds[team_b]

        pa = implied_prob(oa)
        pb = implied_prob(ob)

        # 🔧 normalización (reduce sesgo de cuota)
        pa, pb = normalize_probs(pa, pb)

        # edge real comparativo (no contra 50)
        edge_a = pa - pb
        edge_b = pb - pa

        if edge_a > edge_b:
            pick = team_a
            score = edge_a
        else:
            pick = team_b
            score = edge_b

        # 🧠 penalización por mercado muy equilibrado (ruido)
        market_noise = abs(pa - pb)
        score_adjusted = score + (market_noise * 0.2)

        if score_adjusted < MIN_SCORE:
            continue

        if score_adjusted > 15:
            status = "🔥 STRONG SHARP"
        elif score_adjusted > 10:
            status = "⚡ VALUE"
        else:
            status = "📊 EDGE"

        report += (
            f"⚾ {g['away']} vs {g['home']}\n"
            f"🎯 Pick: {pick}\n"
            f"📈 Score: {score_adjusted:.2f}\n"
            f"🏷 Status: {status}\n\n"
            "----------------\n"
        )

        picks += 1

    if picks == 0:
        report += "⚠️ No value detected (market efficient)"

    send(report)

    print(f"✅ PICKS SENT: {picks}")

    return report
