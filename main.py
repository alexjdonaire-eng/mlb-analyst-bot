import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

r = requests.post(
f"https://api.telegram.org/bot{TOKEN}/sendMessage",
json={
"chat_id": CHAT_ID,
"text": "✅ Nuevo token funcionando correctamente"
}
)

print(r.status_code)
print(r.text)
