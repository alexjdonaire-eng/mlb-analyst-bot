import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


# -----------------------------
# STATS DEL PITCHER
# -----------------------------
def get_pitcher_stats(player_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        data = requests.get(url, timeout=10).json()

        stats = data.get("stats", [])

        if not stats or not stats[0].get("splits"):
            return None, None

        stat = stats[0]["splits"][0]["stat"]

        return stat.get("era"), stat.get("whip")

    except Exception:
        return None, None


# -----------------------------
# PITCHERS DEL JUEGO
# -----------------------------
def get_probable_pitchers(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()

        pitchers = data.get("gameData", {}).get("probablePitchers", {})

        away = pitchers.get("away", {})
        home = pitchers.get("home", {})

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
                "name": away.get("fullName"),
                "era": away_era,
                "whip": away_whip
            },
            "home": {
                "name": home.get("fullName"),
                "era": home_era,
                "whip": home_whip
            }
        }

    except Exception:
        return None


# -----------------------------
# EDGE (COMPARACIÓN)
# -----------------------------
def get_edge(away, home):
    try:
        if not away or not home:
            return "Sin datos suficientes"

        away_era = float(away["era"]) if away["era"] else None
        home_era = float(home["era"]) if home["era"] else None

        away_whip = float(away["whip"]) if away["whip"] else None
        home_whip = float(home["whip"]) if home["whip"] else None

        score_away = 0
        score_home = 0

        if away_era and home_era:
            if away_era < home_era:
                score_away += 1
            else:
                score_home += 1

        if away_whip and home_whip:
            if away_whip < home_whip:
                score_away += 1
            else:
                score_home += 1

        if score_away > score_home:
            return "Ventaja Visitante"
        elif score_home > score_away:
            return "Ventaja Local"
        else:
            return "Juego Parejo"

    except:
        return "Sin ventaja clara"


# -----------------------------
# FORMATO
# -----------------------------
def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD"

    era = p.get("era") if p.get("era") else "N/A"
    whip = p.get("whip") if p.get("whip") else "N/A"

    return f"{p['name']} | ERA: {era} | WHIP: {whip}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()

    mensaje = "⚾ MLB ANALYST BOT ⚾\n\n"

    games = data.get("dates", [])

    if not games:
        mensaje += "No hay juegos hoy."
    else:
        for game in games[0].get("games", []):
            game_pk = game.get("gamePk")

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            pitchers = get_probable_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            edge = get_edge(away, home)

            mensaje += f"⚾ {away_team} vs {home_team}\n"
            mensaje += f"Pitcher Visitante: {format_pitcher(away)}\n"
            mensaje += f"Pitcher Local: {format_pitcher(home)}\n"
            mensaje += f"📊 Edge: {edge}\n"

            mensaje += "\n──────────────────\n\n"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": mensaje},
        timeout=10
    )

    print("Bot ejecutado correctamente")


if __name__ == "__main__":
    main()                "whip": home_whip
            }
        }

    except Exception:
        return None


# -----------------------------
# FORMATO DE TEXTO
# -----------------------------
def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD (no confirmado)"

    name = p.get("name")
    era = p.get("era") if p.get("era") else "N/A"
    whip = p.get("whip") if p.get("whip") else "N/A"

    return f"{name} | ERA: {era} | WHIP: {whip}"


# -----------------------------
# MAIN BOT
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
    main()
