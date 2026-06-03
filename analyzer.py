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

def analyze_games(schedule_data, odds_data):
    report = []
    seen_games = set()

    # Crear diccionario rápido de odds
    odds_dict = {}
    for g in odds_data:
        key = f"{g.get('away_team')}_vs_{g.get('home_team')}"
        odds_dict[key] = g

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

                # Penalizar confianza si hay pitchers desconocidos
                confidence = round(50, 2)
                if home_pitcher["name"] == "TBD" or away_pitcher["name"] == "TBD":
                    confidence -= 8

                # Elegir pick según confianza
                pick = away if confidence >= 50 else home

                # Ajustar totales de carreras según ERA combinada
                try:
                    home_era = float(home_pitcher["ERA"])
                    away_era = float(away_pitcher["ERA"])
                    combined_era = home_era + away_era
                    if combined_era <= 5:
                        total = 7.5
                    elif combined_era <= 7:
                        total = 8.5
                    else:
                        total = 9.5
                except:
                    total = 8.5  # default

                # Hándicap realista
                handicap = -1.5 if pick==away else 1.5
                if confidence < 55:
                    recommended = "NO JUGAR"
                else:
                    recommended = pick

                # Nivel según confianza
                if confidence >= 70:
                    level = "🔥 ELITE"
                elif confidence >= 60:
                    level = "✅ FUERTE"
                elif confidence >= 55:
                    level = "⚠️ LEAN"
                else:
                    level = "🚫 PASAR"

                # Construir reporte
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
