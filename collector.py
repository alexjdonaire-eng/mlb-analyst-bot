import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals"

def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA":"-", "WHIP":"-"}
    try:
        res = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching",
            timeout=15
        )
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]
        return {"ERA": stats.get("era","-"), "WHIP": stats.get("whip","-")}
    except:
        return {"ERA":"-", "WHIP":"-"}

def fetch_market_data():
    try:
        res = requests.get(ODDS_API_URL, timeout=20)
        data = res.json()
        market = {}
        for g in data:
            try:
                home = g["home_team"]
                away = g["away_team"]
                odds = g.get("bookmakers",[{}])[0].get("markets",[])
                h2h = next((m for m in odds if m["key"]=="h2h"), {})
                totals = next((m for m in odds if m["key"]=="totals"), {})
                spreads = next((m for m in odds if m["key"]=="spreads"), {})

                h_move = 0
                if h2h.get("outcomes"):
                    h_price = h2h["outcomes"][0]["price"]
                    a_price = h2h["outcomes"][1]["price"]
                    h_move = a_price - h_price

                market[f"{home}_vs_{away}"] = {
                    "market_move": h_move,
                    "totals": totals.get("outcomes", [{"point":"-","price":"-"}]),
                    "spread": spreads.get("outcomes", [{"point":"-","price":"-"}])
                }
            except:
                continue
        return market
    except:
        return {}

def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    market_data = fetch_market_data()
    games = []

    for day in data.get("dates", []):
        for g in day.get("games", []):
            try:
                home = g["teams"]["home"]["team"]["name"]
                away = g["teams"]["away"]["team"]["name"]

                hp_data = g["teams"]["home"].get("probablePitcher", {})
                ap_data = g["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {"name": hp_data.get("fullName","TBD")}
                home_pitcher.update(fetch_pitcher_stats(hp_data.get("id")))

                away_pitcher = {"name": ap_data.get("fullName","TBD")}
                away_pitcher.update(fetch_pitcher_stats(ap_data.get("id")))

                key = f"{home}_vs_{away}"
                market = market_data.get(key, {"market_move":0,"totals":[],"spread":[]})

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "market_move": market["market_move"],
                    "totals": market["totals"],
                    "spread": market["spread"]
                })
            except:
                continue
    return games

def run():
    print("📡 COLLECTOR V5.17 PRO START")
    games = fetch_mlb_games()
    print(f"📊 Games loaded: {len(games)}")
    return games
