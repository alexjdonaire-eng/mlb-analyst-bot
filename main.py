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

    print("🏦 SHARP MONEY V5.3 CLEAN OUTPUT START")

    games = collector.run()
    report = analyzer.run(games)

    if not report:
        print("❌ No picks found")
        return

    # ordenar por probabilidad
    report = sorted(report, key=lambda x: x["probability"], reverse=True)

    top5 = report[:5]

    print("📡 Sending individual game messages...")

    # =========================
    # 1 GAME = 1 MESSAGE
    # =========================
    for r in report:

        message = (
            f"⚾ {r['game']}\n\n"
            f"🎯 Pick: {r['pick']}\n"
            f"📊 Confianza: {r['probability']}%\n"
            f"📈 Edge: {r['edge']}%\n"
            f"📊 Steam: {r['steam']}\n"
            f"🏷 Nivel: {r['level']}"
        )

        send(message)

    # =========================
    # TOP 5 SUMMARY
    # =========================
    summary = "🏦 MLB SHARP MONEY V5.3\n\n🔥 TOP 5 PICKS\n\n"

    for i, r in enumerate(top5, start=1):
        summary += f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"

    summary += "\n💎 COMBINADA DEL DÍA\n\n"

    for r in report:
        if r["probability"] >= 59:
            summary += f"✅ {r['pick']}\n"

    summary += f"\n🔥 Mejor Pick:\n{top5[0]['pick']} ({top5[0]['probability']}%)"

    send(summary)

    print("✅ Telegram sent")
    print("🏁 CYCLE COMPLETE")


if __name__ == "__main__":
    main()
