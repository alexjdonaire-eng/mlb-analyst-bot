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

    print("🏦 SHARP MONEY V4.5 INSTITUTIONAL START")

    games = collector.run()
    report = analyzer.run(games)

    if not report:
        print("❌ No picks found")
        return

    # Ordenar por probabilidad
    report = sorted(report, key=lambda x: x["probability"], reverse=True)

    top5 = report[:5]
    parlay = [r for r in report if r["probability"] >= 59][:4]

    message = "🏦 MLB SHARP MONEY V4.5\n\n"

    # =========================
    # TOP 5
    # =========================
    message += "🔥 TOP 5 PICKS\n\n"

    for i, r in enumerate(top5, start=1):

        message += (
            f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"
        )

    message += "\n━━━━━━━━━━━━━━\n"

    # =========================
    # GAMES (1 BLOQUE POR JUEGO)
    # =========================
    for r in report:

        message += (
            f"\n⚾ {r['game']}\n"
            f"🎯 Pick: {r['pick']}\n"
            f"📊 Confianza: {r['probability']}%\n"
            f"📈 Edge: {r['edge']}%\n"
            f"🏷 Nivel: {r['level']}\n"
            "━━━━━━━━━━━━━━\n"
        )

    # =========================
    # COMBINADA
    # =========================
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


if __name__ == "__main__":
    main()
