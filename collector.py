import requests

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA": "-", "WHIP": "-"}
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]
        return {
            "ERA": stats.get("era", "-"),
            "WHIP": stats.get("whip", "-")
        }
    except:
        return {"ERA": "-", "WHIP": "-"}

def fetch_mlb_data():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except Exception as e:
        print(f"❌ Error fetching MLB data: {e}")
        return []

    games = []
    dates = data.get("dates", [])
    if not dates:
        return []

    for day in dates:
        for game in day.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]

                home_pitcher_data = game["teams"]["home"].get("probablePitcher", {})
                away_pitcher_data = game["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {
                    "name": home_pitcher_data.get("fullName", "TBD"),
                    **fetch_pitcher_stats(home_pitcher_data.get("id"))
                }

                away_pitcher = {
                    "name": away_pitcher_data.get("fullName", "TBD"),
                    **fetch_pitcher_stats(away_pitcher_data.get("id"))
                }

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "movement": 0,
                    "steam": "⚪ NEUTRAL"
                })

            except Exception as e:
                print(f"❌ Game parse error: {e}")

    return games

def run():
    print("📡 COLLECTOR V5.12 START")
    games = fetch_mlb_data()
    print(f"📊 Games loaded: {len(games)}")
    return games
