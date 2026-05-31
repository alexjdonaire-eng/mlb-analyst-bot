import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Juegos MLB del día
url_mlb = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

respuesta = requests.get(url_mlb).json()

mensaje = "⚾ MLB HOY\n\n"

fechas = respuesta.get("dates", [])

if fechas:
    juegos = fechas[0].get("games", [])

    for juego in juegos:
        visitante = juego["teams"]["away"]["team"]["name"]
        local = juego["teams"]["home"]["team"]["name"]

        mensaje += f"{visitante} vs {local}\n"

else:
    mensaje += "No se encontraron juegos."

# Enviar a Telegram
url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url_telegram,
    json={
        "chat_id": CHAT_ID,
        "text": mensaje
    }
)

print("Mensaje enviado")
