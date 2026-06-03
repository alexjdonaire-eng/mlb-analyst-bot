import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals"


def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA": "-", "WHIP": "-"}

    try:
        res = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching",
            timeout=15
        )
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]

        return {
            "ERA": stats.get("era", "-"),
            "WHIP": stats.get("whip", "-")
        }

    except:
        return {"ERA": "-", "WHIP": "-"}


def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    games = []

    for day in data.get("dates", []):
        for g in day.get("games", []):

            try:
                home = g["teams"]["home"]["team"]["name"]
                away = g["teams"]["away"]["team"]["name"]

                hp = g["teams"]["home"].get("probablePitcher", {})
                ap = g["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {
                    "name": hp.get("fullName", "TBD"),
                    **fetch_pitcher_stats(hp.get("id"))
                }

                away_pitcher = {
                    "name": ap.get("fullName", "TBD"),
                    **fetch_pitcher_stats(ap.get("id"))
                }

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher
                })

            except:
                continue

    return games


def run():
    print("📡 COLLECTOR V5.19 START")
    games = fetch_mlb_games()
    print(f"📊 Games loaded: {len(games)}")
    return games
