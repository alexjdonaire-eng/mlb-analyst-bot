import os
import time
import requests
import collector
import analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOCK_FILE = "bot.lock"


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

    # =========================
    # LOCK SYSTEM (ANTI OVERLAP)
    # =========================
    if os.path.exists(LOCK_FILE):
        print("⛔ BOT LOCKED - previous run still active")
        return

    open(LOCK_FILE, "w").close()

    try:

        print("🏦 SHARP MONEY V5.1 CLEAN ENGINE START")

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
        parlay = [r for r in report if r["probability"] >= 59][:4]

        message = "🏦 MLB SHARP MONEY V5.1\n\n"

        message += "🔥 TOP 5 PICKS\n\n"

        for i, r in enumerate(top5, start=1):
            message += f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"

        message += "\n━━━━━━━━━━━━━━\n"

        for r in report:

            message += (
                f"\n⚾ {r['game']}\n"
                f"🎯 Pick: {r['pick']}\n"
                f"📊 Confianza: {r['probability']}%\n"
                f"📈 Edge: {r['edge']}%\n"
                f"🏷 Nivel: {r['level']}\n"
                "━━━━━━━━━━━━━━\n"
            )

        message += "\n💎 COMBINADA DEL DÍA\n\n"

        for r in parlay:
            message += f"✅ {r['pick']}\n"

        if top5:
            message += (
                f"\n🔥 Mejor Pick:\n"
                f"{top5[0]['pick']} ({top5[0]['probability']}%)"
            )

        send(message)

        print("✅ Telegram sent")
        print("🏁 CYCLE COMPLETE")

    finally:
        # =========================
        # CLEAN EXIT (SIEMPRE LIMPIA LOCK)
        # =========================
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


if __name__ == "__main__":
    main()
