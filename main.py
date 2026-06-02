import os
import requests

# =========================
# VARIABLES
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# DEBUG
# =========================

print("TOKEN EXISTS:", bool(TOKEN))
print("CHAT_ID EXISTS:", bool(CHAT_ID))

# =========================
# TELEGRAM TEST
# =========================

def send_test():

    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN NOT FOUND")
        return

    if not CHAT_ID:
        print("ERROR: TELEGRAM_CHAT_ID NOT FOUND")
        return

    try:

        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": "🧪 TEST FROM RAILWAY"
            },
            timeout=20
        )

        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================
# MAIN
# =========================

def main():

    print("STARTING TEST")

    send_test()

    print("FINISHED")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
