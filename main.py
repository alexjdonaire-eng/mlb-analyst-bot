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


def get_probable_pitchers(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()

        pitchers = data.get("gameData", {}).get("probablePitchers", {})

        away = pitchers.get("away", {})
        home = pitchers.get("home", {})

        away_id = away.get("id")
        home_id = home.get("id")

        away_era, away_whip = None, None
        home_era, home_whip = None, None

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


def get_team_offense():
    try:
        url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
        data = requests.get(url, timeout=10).json()

        offense = {}

        for record in data.get("records", []):
            for team in record.get("teamRecords", []):
                name = team["team"]["name"]
                runs = float(team.get("runsScored", 0))
                games = float(team.get("gamesPlayed", 1))
                offense[name] = runs / games

        return offense

    except:
        return {}


def get_win_probability(away, home, offense):
    try:
        away_score = 50
        home_score = 50

        if away and home:

            if away["era"] and home["era"]:
                diff = float(home["era"]) - float(away["era"])

                if diff > 0.50:
                    away_score += 10
                    home_score -= 10
                elif diff < -0.50:
                    home_score += 10
                    away_score -= 10

            if away["whip"] and home["whip"]:
                diff = float(home["whip"]) - float(away["whip"])

                if diff > 0.15:
                    away_score += 5
                    home_score -= 5
                elif diff < -0.15:
                    home_score += 5
                    away_score -= 5

            away_rpg = offense.get(away.get("team"))
            home_rpg = offense.get(home.get("team"))

            if away_rpg and home_rpg:
                if away_rpg > home_rpg:
                    away_score += 8
                    home_score -= 8
                elif home_rpg > away_rpg:
                    home_score += 8
                    away_score -= 8

        total = away_score + home_score

        return round((away_score / total) * 100, 1), round((home_score / total) * 100, 1)

    except:
        return None, None


def get_confidence(diff):
    if diff >= 12:
        return "🔥 Alta confianza"
    elif diff >= 6:
        return "🟡 Media confianza"
    return "⚖️ Baja confianza"


def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD"

    return f"{p['name']} | ERA: {p['era'] or 'N/A'} | WHIP: {p['whip'] or 'N/A'}"


def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()
    offense = get_team_offense()

    msg = "⚾ MLB ANALYST BOT ⚾\n\n"

    dates = data.get("dates", [])

    if not dates:
        msg += "No hay juegos hoy."
    else:
        for game in dates[0].get("games", []):

            game_pk = game.get("gamePk")

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            pitchers = get_probable_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            if away:
                away["team"] = away_team
            if home:
                home["team"] = home_team

            away_pct, home_pct = get_win_probability(away, home, offense)

            if away_pct is None or home_pct is None:
                continue

            if abs(away_pct - home_pct) < 5:
                continue

            confidence = get_confidence(abs(away_pct - home_pct))

            msg += f"⚾ {away_team} vs {home_team}\n"
            msg += f"Pitcher Visitante: {format_pitcher(away)}\n"
            msg += f"Pitcher Local: {format_pitcher(home)}\n"
            msg += f"📊 Visitante: {away_pct}% | Local: {home_pct}%\n"
            msg += f"🎯 {confidence}\n\n"
            msg += "──────────────────\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

    print("OK")


if __name__ == "__main__":
    main()
