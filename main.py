import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Endpoint principal (juegos del día)
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

def get_probable_pitchers(game_pk):
    """
    Obtiene pitchers desde el feed live (más confiable que schedule)
    """
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()

        pitchers = data.get("gameData", {}).get("probablePitchers", {})

        away = pitchers.get("away", {})
        home = pitchers.get("home", {})

        away_name = away.get("fullName")
        home_name = home.get("fullName")

        return away_name, home_name

    except Exception:
        return None, None


def format_pitcher(name):
    """
    Mejora presentación del dato faltante
    """
    if name:
        return name
    return "TBD (no confirmado)"


def main():
    respuesta = requests.get(SCHEDULE_URL, timeout=10).json()

    mensaje = "⚾ MLB HOY - ANALISTA BOT ⚾\n\n"

    fechas = respuesta.get("dates", [])

    if not fechas:
        mensaje += "No hay juegos programados."
    else:
        juegos = fechas[0].get("games", [])

        for juego in juegos:
            game_pk = juego.get("gamePk")

            visitante = juego["teams"]["away"]["team"]["name"]
            local = juego["teams"]["home"]["team"]["name"]

            away_pitcher, home_pitcher = get_probable_pitchers(game_pk)

            mensaje += f"⚾ {visitante} vs {local}\n"

            mensaje += f"Pitcher Visitante: {format_pitcher(away_pitcher)}\n"
            mensaje += f"Pitcher Local: {format_pitcher(home_pitcher)}\n"

            mensaje += "\n──────────────────\n\n"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": mensaje
        },
        timeout=10
    )

    print("Mensaje enviado correctamente")


if __name__ == "__main__":
    main()
