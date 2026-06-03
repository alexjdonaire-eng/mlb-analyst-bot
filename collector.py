import requests
from datetime import datetime

# =========================
# CONFIG API (PUEDES CAMBIARLA)
# =========================
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

# =========================
# FUNCIÓN: obtener datos MLB
# =========================
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

                # =========================
                # PITCHERS PROBABLES
                # =========================
                home_pitcher_data = game["teams"]["home"].get("probablePitcher", {})
                away_pitcher_data = game["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {
                    "name": home_pitcher_data.get("fullName", "TBD"),
                    "ERA": fetch_pitcher_stats(home_pitcher_data.get("id")).get("era", "-"),
                    "WHIP": fetch_pitcher_stats(home_pitcher_data.get("id")).get("whip", "-")
                }

                away_pitcher = {
                    "name": away_pitcher_data.get("fullName", "TBD"),
                    "ERA": fetch_pitcher_stats(away_pitcher_data.get("id")).get("era", "-"),
                    "WHIP": fetch_pitcher_stats(away_pitcher_data.get("id")).get("whip", "-")
                }

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "movement": 0,   # placeholder (puedes conectar odds API luego)
                    "steam": "⚪ NEUTRAL"
                })

            except Exception as e:
                print(f"❌ Game parse error: {e}")

    return games

# =========================
# FUNCIÓN: stats pitcher
# =========================
def fetch_pitcher_stats(player_id):

    if not player_id:
        return {"era": "-", "whip": "-"}

    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"

    try:
        res = requests.get(url, timeout=15)
        data = res.json()

        stats = data["stats"][0]["splits"][0]["stat"]

        return {
            "era": stats.get("era", "-"),
            "whip": stats.get("whip", "-")
        }

    except:
        return {"era": "-", "whip": "-"}

# =========================
# MAIN CALL
# =========================
def run():
    print("📡 COLLECTOR V5.11 START")
    games = fetch_mlb_data()
    print(f"📊 Games loaded: {len(games)}")
    return games
