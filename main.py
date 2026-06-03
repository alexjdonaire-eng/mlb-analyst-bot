import os
import requests
import collector
import analyzer

# =========================
# TELEGRAM CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================
# SEND MESSAGE
# =========================
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


# =========================
# FORMAT GAME MESSAGE
# =========================
def format_game(r):

    return (
        f"⚾ {r['game']}\n\n"
        f"🎯 Pick: {r['pick']}\n"
        f"📊 Confianza: {r['probability']}%\n"
        f"📈 Edge: {r['edge']}%\n"
        f"📡 Steam: {r['steam']}\n"
        f"🧾 Pitchers: {r.get('pitcher','TBD')}\n"
        f"🧠 Score: {r.get('score','N/A')}\n"
        f"🏷 Nivel: {r['level']}\n"
        "━━━━━━━━━━━━━━"
    )


# =========================
# MAIN
# =========================
def main():

    print("🏦 SHARP MONEY V5.7 START")

    # 1. COLLECT DATA
    games = collector.run()

    # 2. ANALYZE DATA (CORRECT IMPORT)
    report = analyzer.run(games)

    print("📊 Games loaded:", len(report))

    if not report:
        print("❌ No report generated")
        return

    # 3. SORT BY SCORE OR PROBABILITY
    report = sorted(
        report,
        key=lambda x: x.get("score", x["probability"]),
        reverse=True
    )

    # =========================
    # SEND EACH GAME (1 MESSAGE)
    # =========================
    for r in report:

        message = format_game(r)
        send(message)

        print(f"✅ Sent: {r['game']}")

    # =========================
    # TOP PICKS SUMMARY
    # =========================
    top5 = report[:5]

    summary = "🏦 MLB SHARP MONEY V5.7\n\n🔥 TOP 5 PICKS\n\n"

    for i, r in enumerate(top5, 1):
        summary += f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"

    summary += "\n💎 COMBINADA DEL DÍA\n\n"

    for r in report:
        if r["probability"] >= 59:
            summary += f"✅ {r['pick']}\n"

    if top5:
        summary += f"\n🔥 Mejor Pick:\n{top5[0]['pick']} ({top5[0]['probability']}%)"

    send(summary)

    print("🏁 Cycle complete")


if __name__ == "__main__":
    main()
