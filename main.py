import os
import requests
import collector
import analyzer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=20
    )

def main():
    print("🏦 MLB SHARP MONEY V5.4 START")

    games = collector.run()
    report = analyzer.run(games)

    if report:
        for r in report:
            message = (
                f"⚾ {r['game']}\n"
                f"🎯 Pick: {r['pick']}\n"
                f"📊 Confianza: {r['probability']}%\n"
                f"📈 Edge: {r['edge']}%\n"
                f"📊 Steam: {r['steam']}\n"
                f"🏷 Nivel: {r['level']}{r['pitcher']}\n"
                f"━━━━━━━━━━━━━━"
            )
            send(message)
            print("✅ Telegram sent:", r['pick'])

    print("🏁 CYCLE COMPLETE")

if __name__ == "__main__":
    main()
