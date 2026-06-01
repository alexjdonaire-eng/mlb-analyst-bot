import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message():
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": "🚀 BOT OK - SIN ERRORES DE INDENTACIÓN"
        }
    )
    print(r.status_code)
    print(r.text)

if __name__ == "__main__":
    send_message()
