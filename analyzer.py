import requests
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_EV = 4.0  # sharp threshold

def implied_prob(odds):
    return (1 / odds) * 100

def run(games):

    print("🧠 ANALYZER START")

    report = "🏦 SHARP MONEY BOT V3\n\n"
    picks = 0

    for g in games:

        odds = g["odds"]

        if len(odds) < 2:
            continue

        # favorito por mercado
        fav = min(odds, key=odds.get)
        dog = max(odds, key=odds.get)

        fav_odds = odds[fav]
        dog_odds = odds[dog]

        fav_prob = implied_prob(fav_odds)
        dog_prob = implied_prob(dog_odds)

        # EV simplificado (edge del underdog o favorito subvaluado)
        ev_fav = fav_prob - 50
        ev_dog = dog_prob - 50

        best_pick = fav
        best_ev = ev_fav

        if ev_dog > ev_fav:
            best_pick = dog
            best_ev = ev_dog

        if best_ev < MIN_EV:
            continue

        if best_ev > 10:
            status = "🔥 SHARP"
        elif best_ev > 6:
            status = "⚡ VALUE"
        else:
            status = "📊 EDGE"

        report += (
            f"⚾ {g['away']} vs {g['home']}\n"
            f"🎯 Pick: {best_pick}\n"
            f"📊 EV: {best_ev:.2f}%\n"
            f"🏷 Status: {status}\n\n"
            "----------------\n"
        )

        picks += 1

    if picks == 0:
        report += "⚠️ No sharp value detected"

    send(report)

    print(f"✅ PICKS SENT: {picks}")

    return report


def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=15
        )
        print("📤 Telegram sent")
    except Exception as e:
        print(f"❌ Telegram error: {e}")
