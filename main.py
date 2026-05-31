import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


def get_pitcher_stats(player_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        data = requests.get(url, timeout=10).json()

        stats = data.get("stats", [])
        if not stats or not stats[0].get("splits"):
            return None, None

        stat = stats[0]["splits"][0]["stat"]
        return stat.get("era"), stat.get("whip")

    except:
        return None, None


def get_pitchers(game_pk):
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

    except:
        return None


def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD"

    era = p.get("era") or "N/A"
    whip = p.get("whip") or "N/A"

    return f"{p['name']} | ERA: {era} | WHIP: {whip}"


def get_edge(away, home):
    try:
        if not away or not home:
            return "Sin datos suficientes"

        score_away = 0
        score_home = 0

        if away["era"] and home["era"]:
            if float(away["era"]) < float(home["era"]):
                score_away += 1
            else:
                score_home += 1

        if away["whip"] and home["whip"]:
            if float(away["whip"]) < float(home["whip"]):
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
        return "Sin análisis"


def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()

    msg = "⚾ MLB ANALYST BOT ⚾\n\n"

    dates = data.get("dates", [])
    if not dates:
        msg += "No hay juegos hoy."
    else:
        for game in dates[0].get("games", []):
            game_pk = game.get("gamePk")

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            pitchers = get_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            edge = get_edge(away, home)

            msg += f"⚾ {away_team} vs {home_team}\n"
            msg += f"Pitcher Visitante: {format_pitcher(away)}\n"
            msg += f"Pitcher Local: {format_pitcher(home)}\n"
            msg += f"📊 Edge: {edge}\n\n"
            msg += "──────────────────\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

    print("OK")


if __name__ == "__main__":
    main()
