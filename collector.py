import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h"

def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA":"-", "WHIP":"-"}
    try:
        res = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching", timeout=15)
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]
        return {"ERA": stats.get("era","-"), "WHIP": stats.get("whip","-")}
    except:
        return {"ERA":"-", "WHIP":"-"}

def fetch_market_moves():
    try:
        res = requests.get(ODDS_API_URL, timeout=15)
        data = res.json()
        moves = {}
        for g in data:
            try:
                home = g["home_team"]
                away = g["away_team"]
                h_odds = g["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]
                a_odds = g["bookmakers"][0]["markets"][0]["outcomes"][1]["price"]
                move = a_odds - h_odds
                moves[f"{home}_vs_{away}"] = move
            except:
                continue
        return moves
    except:
        return {}

def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    moves = fetch_market_moves()
    games = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]

                hp_data = game["teams"]["home"].get("probablePitcher", {})
                ap_data = game["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {"name": hp_data.get("fullName","TBD")}
                home_pitcher.update(fetch_pitcher_stats(hp_data.get("id")))

                away_pitcher = {"name": ap_data.get("fullName","TBD")}
                away_pitcher.update(fetch_pitcher_stats(ap_data.get("id")))

                key = f"{home}_vs_{away}"
                market_move = moves.get(key, 0)

                if market_move >= 5:
                    steam = "🔥 SHARP MONEY IN"
                elif market_move <= -5:
                    steam = "⚪ PUBLIC HEAVY"
                else:
                    steam = "⚪ NEUTRAL"

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "movement": market_move,
                    "steam": steam
                })
            except:
                continue
    return games

def run():
    print("📡 COLLECTOR V5.15 START")
    games = fetch_mlb_games()
    print(f"📊 Games loaded: {len(games)}")
    return games
