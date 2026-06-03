import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

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

def fetch_odds():
    if not ODDS_API_KEY:
        print("❌ ODDS_API_KEY not set")
        return {}
    try:
        res = requests.get(f"{ODDS_API_URL}?regions=us&oddsFormat=decimal", timeout=15, headers={"Authorization": f"Bearer {ODDS_API_KEY}"})
        data = res.json()
        odds_map = {}
        for g in data:
            home = g["home_team"]
            away = g["away_team"]
            movement = 0
            steam = "⚪ NEUTRAL"
            # Detect Sharp Money
            if "bookmakers" in g and len(g["bookmakers"]) > 0:
                for b in g["bookmakers"]:
                    if "markets" in b:
                        for m in b["markets"]:
                            if "outcomes" in m:
                                for o in m["outcomes"]:
                                    if o.get("pointSpread",0) > 0.1:
                                        steam = "🔥 SHARP MONEY IN"
                                        movement = o.get("price",0)
            odds_map[(home, away)] = {"movement": movement, "steam": steam}
        return odds_map
    except Exception as e:
        print(f"❌ Odds fetch error: {e}")
        return {}

def fetch_mlb_data():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except Exception as e:
        print(f"❌ Error fetching MLB data: {e}")
        return []

    games = []
    odds_data = fetch_odds()
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

                movement, steam = 0, "⚪ NEUTRAL"
                if (home, away) in odds_data:
                    movement = odds_data[(home, away)]["movement"]
                    steam = odds_data[(home, away)]["steam"]

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "movement": movement,
                    "steam": steam
                })

            except Exception as e:
                print(f"❌ Game parse error: {e}")

    return games

def run():
    print("📡 COLLECTOR V5.13 START")
    games = fetch_mlb_data()
    print(f"📊 Games loaded: {len(games)}")
    return games
