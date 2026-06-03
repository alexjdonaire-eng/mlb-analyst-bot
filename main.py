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

    if report:

        message = "🏦 MLB PICKS\n\n"

        for r in report:

            message += (
                f"⚾ {r['game']}\n"
                f"🎯 {r['pick']}\n"
                f"📊 {r['probability']}%\n"
                f"📈 Edge: {r['edge']}%\n\n"
            )

        send(message)

        print("✅ Telegram sent")

    print("🏁 CYCLE COMPLETE")


if __name__ == "__main__":
    main()
