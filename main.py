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

    mensaje += f"⚾ {visitante} vs {local}\n"

    away_pitcher = juego["teams"]["away"].get("probablePitcher")
    home_pitcher = juego["teams"]["home"].get("probablePitcher")

    if away_pitcher:
        mensaje += f"Visitante: {away_pitcher['fullName']}\n"
    else:
        mensaje += "Visitante: Por confirmar\n"

    if home_pitcher:
        mensaje += f"Local: {home_pitcher['fullName']}\n"
    else:
        mensaje += "Local: Por confirmar\n"

    mensaje += "\n─────────────\n\n"
