import requests

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

def analyze_games(schedule_data):
    report = []
    seen_games = set()

    for day in schedule_data.get("dates", []):
        for game in day.get("games", []):
            try:
                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]
                game_id = f"{away}_vs_{home}"
                if game_id in seen_games:
                    continue
                seen_games.add(game_id)

                hp = game["teams"]["home"].get("probablePitcher", {})
                ap = game["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {"name": hp.get("fullName","TBD")}
                home_pitcher.update(fetch_pitcher_stats(hp.get("id")))

                away_pitcher = {"name": ap.get("fullName","TBD")}
                away_pitcher.update(fetch_pitcher_stats(ap.get("id")))

                # Confianza base
                confidence = 50
                if home_pitcher["name"]=="TBD" or away_pitcher["name"]=="TBD":
                    confidence -= 8

                # Elegir ganador
                pick = away if confidence >= 50 else home

                # Ajustar total de carreras
                try:
                    home_era = float(home_pitcher["ERA"])
                    away_era = float(away_pitcher["ERA"])
                    combined_era = home_era + away_era
                    total = 7.5 if combined_era <= 5 else (8.5 if combined_era <=7 else 9.5)
                except:
                    total = 8.5

                # Hándicap
                handicap = -1.5 if pick==away else 1.5

                # Jugada recomendada
                recommended = pick if confidence >= 55 else "NO JUGAR"

                # Nivel
                if confidence >= 70:
                    level = "🔥 ELITE"
                elif confidence >= 60:
                    level = "✅ FUERTE"
                elif confidence >= 55:
                    level = "⚠️ LEAN"
                else:
                    level = "🚫 PASAR"

                report.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "pick": pick,
                    "confidence": confidence,
                    "total": total,
                    "handicap": handicap,
                    "level": level,
                    "recommended": recommended
                })
            except:
                continue

    return report
