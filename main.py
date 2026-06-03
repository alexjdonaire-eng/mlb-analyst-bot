import os
import requests
import collector
import analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================
# TELEGRAM SEND
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
# FORMAT GAME (V5.8)
# =========================
def format_game(r):

    return (
        f"⚾ {r['game']}\n\n"
        f"🎯 Pick: {r['pick']}\n"
        f"📊 Confianza: {r['probability']}%\n"
        f"📈 Edge: {r['edge']}%\n"
        f"📡 Steam: {r.get('steam','⚪ NEUTRAL')}\n"
        f"📉 Market Move: {r.get('movement','N/A')}\n"
        f"🧾 Pitchers: {r.get('pitcher','TBD')}\n"
        f"🧠 Score: {r.get('score','N/A')}\n"
        f"🏷 Nivel: {r['level']}\n"
        "━━━━━━━━━━━━━━"
    )


# =========================
# MAIN ENGINE
# =========================
def main():

    print("🏦 SHARP MONEY V5.8 FULL PRO START")

    # 1. COLLECT
    games = collector.run()

    # 2. ANALYZE (V5.8 EXPECTS ENRICHED DATA)
    report = analyzer.run(games)

    print("📊 Games loaded:", len(report))

    if not report:
        print("❌ No report generated")
        return

    # =========================
    # SORT BY EDGE + MARKET QUALITY
    # =========================
    report = sorted(
        report,
        key=lambda x: (
            x.get("score", x["probability"]) +
            x.get("edge", 0) * 0.5 +
            (2 if x.get("steam") == "🔥 SHARP MONEY IN" else 0) +
            (1.5 if x.get("movement", 0) > 2 else 0)
        ),
        reverse=True
    )

    # =========================
    # SEND EACH GAME (1 MSG)
    # =========================
    for r in report:

        msg = format_game(r)
        send(msg)

        print(f"✅ Sent: {r['game']}")

    # =========================
    # TOP PICKS SUMMARY (V5.8)
    # =========================
    top5 = report[:5]

    summary = "🏦 MLB SHARP MONEY V5.8 FULL PRO\n\n🔥 TOP 5 MARKET PICKS\n\n"

    for i, r in enumerate(top5, 1):
        summary += f"{i}️⃣ {r['pick']} ({r['probability']}%)\n"

    summary += "\n💎 COMBINADA DEL DÍA (FILTERED EV+)\n\n"

    for r in report:
        if r["probability"] >= 59 and r.get("edge", 0) >= 7:
            summary += f"✅ {r['pick']}\n"

    if top5:
        summary += f"\n🔥 BEST VALUE PICK:\n{top5[0]['pick']} ({top5[0]['probability']}%)"

    send(summary)

    print("🏁 V5.8 cycle complete")


if __name__ == "__main__":
    main()
