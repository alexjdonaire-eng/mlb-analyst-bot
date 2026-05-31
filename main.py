import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


# -----------------------------
# OBTENER STATS DEL PITCHER
# -----------------------------
def get_pitcher_stats(player_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        data = requests.get(url, timeout=10).json()

        splits = data["stats"][0]["splits"]

        if not splits:
            return None, None

        stat = splits[0]["stat"]

        era = stat.get("era")
        whip = stat.get("whip")

        return era, whip

    except Exception:
        return None, None


# -----------------------------
# PITCHERS (nombre + stats)
# -----------------------------
def get_probable_pitchers(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()

        pitchers = data.get("gameData", {}).get("probablePitchers", {})

        away = pitchers.get("away", {})
        home = pitchers.get("home", {})

        away_name = away.get("fullName")
        home_name = home.get("fullName")

        away_id = away.get("id")
        home_id = home.get("id")

        away_era, away_whip = (None, None)
        home_era, home_whip = (None, None)

        if away_id:
            away_era, away_whip = get_pitcher_stats(away_id)

        if home_id:
            home_era, home_whip = get_pitcher_stats(home_id)

        return {
            "away": {
                "name": away_name,
                "era": away_era,
                "whip": away_whip
            },
            "home": {
                "name": home_name,
                "era": home_era,
                "whip": home_whip
            }
        }

    except Exception:
        return None


# -----------------------------
# FORMATO LIMPIO
# -----------------------------
def format_pitcher(p):
    if not p or not p["name"]:
        return "TBD (no confirmado)"

    name = p["name"]
    era = p["era"] if p["era"] else "N/A"
    whip = p["whip"] if p["whip"] else "N/A"

    return f"{name} | ERA: {era} | WHIP: {whip}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    respuesta = requests.get(SCHEDULE_URL, timeout=10).json()

    mensaje = "⚾ MLB ANALYST BOT ⚾\n\n"

    fechas = respuesta.get("dates", [])

    if not fechas:
        mensaje += "No hay juegos programados."
    else:
        juegos = fechas[0].get("games", [])

        for juego in juegos:
            game_pk = juego.get("gamePk")

            visitante = juego["teams"]["away"]["team"]["name"]
            local = juego["teams"]["home"]["team"]["name"]

            pitchers = get_probable_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            mensaje += f"⚾ {visitante} vs {local}\n"

            mensaje += f"Pitcher Visitante: {format_pitcher(away)}\n"
            mensaje += f"Pitcher Local: {format_pitcher(home)}\n"

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
    main()        url,
        json={
            "chat_id": CHAT_ID,
            "text": mensaje
        },
        timeout=10
    )

    print("Mensaje enviado correctamente")


if __name__ == "__main__":
    main()
