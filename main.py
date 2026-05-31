import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

mensaje = """
⚾ MLB Analyst Bot

✅ Conexión exitosa

El bot está funcionando correctamente en Railway.
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": mensaje
    }
)

print("Mensaje enviado")
