import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,totals,spreads"

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

def fetch_market_data():
    try:
        res = requests.get(ODDS_API_URL, timeout=15)
        data = res.json()
        markets = {}
        for g in data:
            try:
                home = g["home_team"]
                away = g["away_team"]
                mkt = g["bookmakers"][0]["markets"]
                # ML
                h_ml = a_ml = 0
                total = total_conf = 0
                spread = ""
                for m in mkt:
                    if m["key"] == "h2h":
                        h_ml = m["outcomes"][0]["price"]
                        a_ml = m["outcomes"][1]["price"]
                    elif m["key"] == "totals":
                        total = m["outcomes"][0]["point"]  # ejemplo Over/Under
                        total_conf = 60  # placeholder, podemos hacer cálculo más avanzado
                    elif m["key"] == "spreads":
                        spread = m["outcomes"][0]["point"]
                markets[f"{home}_vs_{away}"] = {
                    "h_ml": h_ml, "a_ml": a_ml,
                    "total": total,
                    "spread": spread
                }
            except:
                continue
        return markets
    except:
        return {}

def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    markets = fetch_market_data()
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
                mkt = markets.get(key, {})
                h_ml = mkt.get("h_ml",0)
                a_ml = mkt.get("a_ml",0)
                total = mkt.get("total","-")
                spread = mkt.get("spread","-")

                # Score simple
                score = (float(home_pitcher.get("ERA",4.5)) + float(home_pitcher.get("WHIP",1.5))) - \
                        (float(away_pitcher.get("ERA",4.5)) + float(away_pitcher.get("WHIP",1.5)))

                pick = home if score<0 else away
                confidence = min(max(abs(score)*12 + 50,45),75)
                level = "🔥 ELITE" if confidence>=64 else "✅ FUERTE" if confidence>=58 else "⚠️ LEAN"

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "pick": pick,
                    "confidence": round(confidence,2),
                    "level": level,
                    "total": total,
                    "spread": spread
                })
            except:
                continue
    return games

def run():
    print("📡 COLLECTOR V5.16 START")
    games = fetch_mlb_games()
    print(f"📊 Juegos cargados: {len(games)}")
    return games
