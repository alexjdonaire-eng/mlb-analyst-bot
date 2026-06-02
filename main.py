import os
import json
import requests

HISTORY_FILE = "market_history.jsonl"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM
# =========================

def send(msg):

    print("TOKEN:", TOKEN)
    print("CHAT_ID:", CHAT_ID)

    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN no encontrado")
        return

    if not CHAT_ID:
        print("ERROR: TELEGRAM_CHAT_ID no encontrado")
        return

    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

# =========================
# LOAD HISTORY
# =========================

def load_history():

    data = []

    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                data.append(json.loads(line))
    except Exception as e:
        print("History error:", e)

    return data

# =========================
# MAIN
# =========================

def main():

    history = load_history()

    report = (
        "🏦 MLB ANALYZER\n\n"
        f"Snapshots encontrados: {len(history)}\n"
    )

    send(report)

    print("ANALYZER FINISHED")

if __name__ == "__main__":
    main()
