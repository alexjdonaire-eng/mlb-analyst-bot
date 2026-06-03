import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SCORE = 11.0


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


def implied_prob(odds):
    return (1 / odds) * 100


def normalize_two(a, b):
    total = a + b
    return (a / total) * 100, (b / total) * 100


# 🧠 pseudo volatility (proxy sin histórico real de lines movement)
def volatility_proxy(p1, p2):
    return abs(p1 - p2) / (p1 + p2)


def run(games):

    print("🏦 SHARP MONEY V5 HEDGE FUND START")

    report = "🏦 SHARP MONEY V5 — HEDGE FUND MODEL\n\n"

    picks = 0

    for g in games:

        odds = g.get("odds", {})

        if len(odds) < 2:
            continue

        teams = list(odds.keys())

        # 📊 implied probability
        probs = {t: implied_prob(o) for t, o in odds.items()}

        # 🔧 normalize market
        p1, p2 = normalize_two(probs[teams[0]], probs[teams[1]])

        probs[teams[0]] = p1
        probs[teams[1]] = p2

        fav = max(probs, key=probs.get)
        dog = min(probs, key=probs.get)

        fav_p = probs[fav]
        dog_p = probs[dog]

        # 📉 EDGE
        edge = abs(fav_p - dog_p)

        # 🧠 MARKET PRESSURE (dominancia del favorito)
        pressure = fav_p / (fav_p + dog_p)

        # 🧠 VOLATILITY PROXY (clave V5)
        vol = volatility_proxy(fav_p, dog_p)

        # 🧠 CONSENSUS STABILITY SCORE
        stability = 1 - vol

        # 🧠 "CLOSING LINE PROXY"
        # simulamos que el mercado eficiente empuja hacia equilibrio
        clv_proxy = edge * stability * (1 + pressure)

        # 🧠 FINAL SHARP SCORE V5
        score = (
            edge * 0.35 +
            clv_proxy * 0.45 +
            stability * 10 * 0.2
        )

        pick = fav

        if score < MIN_SCORE:
            continue

        # 🧠 classification
        if score > 20:
            tag = "🔥 HEDGE FUND SHARP"
        elif score > 16:
            tag = "⚡ INSTITUTIONAL EDGE"
        elif score > 13:
            tag = "📊 SHARP VALUE"
        else:
            tag = "📈 WEAK EDGE"

        report += (
            f"⚾ {g.get('away')} vs {g.get('home')}\n"
            f"🎯 Pick: {pick}\n"
            f"📊 Score V5: {score:.2f}\n"
            f"📉 Edge: {edge:.2f}\n"
            f"🧠 Pressure: {pressure:.2f}\n"
            f"📊 Stability: {stability:.2f}\n"
            f"📈 CLV Proxy: {clv_proxy:.2f}\n"
            f"🏷 Status: {tag}\n\n"
            "----------------------\n"
        )

        picks += 1

    if picks == 0:
        report += "⚠️ No hedge fund edge detected (market efficient zone)"

    send(report)

    print(f"✅ V5 PICKS SENT: {picks}")

    return report
