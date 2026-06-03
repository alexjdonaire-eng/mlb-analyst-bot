import requests
import os

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

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
        return {"ERA": stats.get("era", "-"), "WHIP": stats.get("whip", "-")}
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

                home_pitcher = {"name": hp.get("fullName", "TBD"), **fetch_pitcher_stats(hp.get("id"))}
                away_pitcher = {"name": ap.get("fullName", "TBD"), **fetch_pitcher_stats(ap.get("id"))}

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher
                })
            except:
                continue
    return games

def analyze_games(games):
    analyzed = []
    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        
        # Simulación de predicciones (reemplazar por tu lógica real)
        winner = {"team": home, "prob": 55}
        total = {"line": 8.5, "prob": 60, "type": "Alta"}
        handicap = {"line": f"{home} -1.5", "prob": 58}

        picks = [
            {"type": "Ganador", "value": winner["team"], "prob": winner["prob"]},
            {"type": "Total Alta" if total["type"]=="Alta" else "Total Baja", "value": f"{total['line']}", "prob": total["prob"]},
            {"type": "Hándicap", "value": handicap["line"], "prob": handicap["prob"]}
        ]
        best_pick = max(picks, key=lambda x: x["prob"])
        
        level = "✅ FUERTE" if best_pick["prob"] >= 65 else ("⚠️ LEAN" if best_pick["prob"] >= 50 else "🚫 PASAR")
        confidence = best_pick["prob"]
        
        analyzed.append({
            "home_team": home,
            "away_team": away,
            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,
            "predicted_winner": winner,
            "predicted_total": total,
            "predicted_handicap": handicap,
            "top_pick_type": best_pick["type"],
            "top_pick_value": best_pick["value"],
            "confidence": confidence,
            "level": level
        })
    return analyzed
