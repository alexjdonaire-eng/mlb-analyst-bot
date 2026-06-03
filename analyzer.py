import os
import requests
import math

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 💰 BANKROLL SIMULADO (puedes cambiarlo)
BANKROLL = 1000.0

# 🎯 control de riesgo (conservador hedge fund)
RISK_CAP = 0.025  # 2.5% max por pick


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


def implied_prob(odds):
    return (1 / odds) * 100


def normalize(a, b):
    total = a + b
    return (a / total) * 100, (b / total) * 100


# 🧠 Kelly simplificado (clave V6)
def kelly_fraction(prob, odds):
    b = odds - 1
    q = 1 - prob
    return max((b * prob - q) / b, 0)


# 🧠 risk score (evita overexposure)
def risk_adjustment(edge, confidence):
    return edge * confidence


def run(games):

    print("🏦 SHARP MONEY V6 HEDGE FUND PORTFOLIO START")

    candidates = []

    for g in games:

        odds = g.get("odds", {})
        if len(odds) < 2:
            continue

        teams = list(odds.keys())

        # 📊 implied probabilities
        probs = {t: implied_prob(o) for t, o in odds.items()}

        # 🔧 normalize market
        p1, p2 = normalize(probs[teams[0]], probs[teams[1]])
        probs[teams[0]] = p1
        probs[teams[1]] = p2

        fav = max(probs, key=probs.get)
        dog = min(probs, key=probs.get)

        fav_p = probs[fav] / 100
        dog_p = probs[dog] / 100

        fav_odds = odds[fav]

        # 📉 EDGE
        edge = abs(probs[fav] - probs[dog])

        # 🧠 confidence model
        confidence = edge / 20  # normalized rough proxy

        # 🧠 kelly sizing
        kelly = kelly_fraction(fav_p, fav_odds)

        # 🧠 risk-adjusted score
        score = risk_adjustment(edge, confidence)

        candidates.append({
            "game": g,
            "pick": fav,
            "edge": edge,
            "confidence": confidence,
            "kelly": kelly,
            "score": score,
            "odds": fav_odds
        })

    # 🧠 sort by institutional priority
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 🔥 portfolio selection (TOP N ONLY)
    top = candidates[:5]

    if not top:
        send("⚠️ No institutional edges detected (V6 portfolio empty)")
        return

    report = "🏦 SHARP MONEY V6 — HEDGE FUND PORTFOLIO\n\n"
    report += f"💰 BANKROLL: ${BANKROLL}\n"
    report += f"📊 PICKS SELECTED: {len(top)}\n\n"

    total_alloc = 0

    for c in top:

        # 🧠 position sizing (risk capped Kelly)
        raw_kelly = c["kelly"]
        stake = BANKROLL * min(raw_kelly, RISK_CAP)

        total_alloc += stake

        g = c["game"]

        report += (
            f"⚾ {g['away']} vs {g['home']}\n"
            f"🎯 Pick: {c['pick']}\n"
            f"📊 Edge: {c['edge']:.2f}\n"
            f"🧠 Confidence: {c['confidence']:.2f}\n"
            f"📈 Kelly: {c['kelly']:.4f}\n"
            f"💰 Stake: ${stake:.2f}\n"
            f"🏷 Odds: {c['odds']}\n\n"
            "----------------------\n"
        )

    # 🧠 capital check
    report += f"\n💼 TOTAL ALLOCATED: ${total_alloc:.2f}"
    report += f"\n🧯 RISK UTILIZATION: {total_alloc / BANKROLL:.2%}"

    send(report)

    print(f"✅ V6 PORTFOLIO SENT | PICKS: {len(top)}")
