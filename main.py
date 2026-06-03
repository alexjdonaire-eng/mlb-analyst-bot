import os
import requests
import collector
import analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send(msg):

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=20
        )
    except Exception as e:
        print("❌ Telegram error:", e)


def main():

    print("🏦 SHARP MONEY V5.4 CLEAN ENGINE START")

    games = collector.run()
    report = analyzer.run(games)

    print("🏁 CYCLE COMPLETE")

    if not report:
        print("❌ No report generated")
        return

    report = sorted(report, key=lambda x: x["probability"], reverse=True)

    top5 = report[:5]

    # =========================
    # ENVIAR PICKS INDIVIDUALES
    # =========================
    for r in report:

        message = (
            f"⚾ {r['game']}\n\n"
            f"🎯 Pick: {r['pick']}\n"
            f"📊 Confianza: {r['probability']}%\n"
            f"📈 Edge: {r['edge']}%\n"
            f"📊 Steam: {r['steam']}\n"
            f"🏷 Nivel: {r['level']}\n"
        )

        send(message)

    # =========================
    # TOP 5 SUMMARY
    # =========================
    summary = "🏦 MLB SHARP MONEY V5.4\n\n🔥 TOP 5 PICKS\n\n"

    for i, r in enumerate(top5, 1):
        summary += f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"

    summary += "\n💎 COMBINADA DEL DÍA\n\n"

    for r in report:
        if r["probability"] >= 59:
            summary += f"✅ {r['pick']}\n"

    if top5:
        summary += f"\n🔥 Mejor Pick:\n{top5[0]['pick']} ({top5[0]['probability']}%)"

    send(summary)

    print("✅ Telegram sent")


if __name__ == "__main__":
    main()
