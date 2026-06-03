import os
import requests
import collector
import analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=20
    )


def main():

    print("🏦 SHARP MONEY V4 INSTITUTIONAL START")

    games = collector.run()
    report = analyzer.run(games)

    if not report:
        print("❌ No picks found")
        return

    report = sorted(
        report,
        key=lambda x: x["probability"],
        reverse=True
    )

    top5 = report[:5]
    parlay = report[:4]

    message = "🏦 MLB SHARP MONEY\n\n"

    message += "🔥 TOP 5 PICKS\n\n"

    for i, r in enumerate(top5, start=1):

        message += (
            f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"
        )

    message += "\n━━━━━━━━━━━━━━\n\n"

    for r in report:

        message += (
            f"⚾ {r['game']}\n"
            f"🎯 {r['pick']}\n"
            f"📊 Confianza: {r['probability']}%\n"
            f"📈 Edge: {r['edge']}%\n\n"
        )

    message += "━━━━━━━━━━━━━━\n\n"
    message += "💎 COMBINADA DEL DÍA\n\n"

    for r in parlay:

        message += f"✅ {r['pick']}\n"

    message += (
        f"\n🔥 Mejor Pick:\n"
        f"{top5[0]['pick']} ({top5[0]['probability']}%)"
    )

    send(message)

    print("✅ Telegram sent")
    print("🏁 CYCLE COMPLETE")


if __name__ == "__main__":
    main()
