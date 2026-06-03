import requests

def fetch_pitcher_stats(player_id):
    """Obtiene estadísticas de lanzador desde MLB Stats API."""
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

def analyze_games(schedule_data, odds_data=None):
    """Analiza todos los juegos del día y devuelve reporte completo."""
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
                confidence = 50.0
                if home_pitcher["name"] == "TBD" or away_pitcher["name"] == "TBD":
                    confidence -= 10

                # Ajustar por ERA combinada
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

                    # Aumentar confianza si lanzadores muy buenos
                    if home_era < 3 and away_era < 3:
                        confidence += 15
                    elif home_era < 4 and away_era < 4:
                        confidence += 10
                except:
                    total = 8.5

                # Determinar pick según confianza y ERA
                pick = away if confidence >= 55 else home

                # Hándicap automático
                handicap = -1.5 if pick==away else 1.5

                # Nivel según confianza
                if confidence >= 70:
                    level = "🔥 ELITE"
                elif confidence >= 60:
                    level = "✅ FUERTE"
                elif confidence >= 55:
                    level = "⚠️ LEAN"
                else:
                    level = "🚫 PASAR"

                # Jugada recomendada
                recommended = pick if confidence >= 55 else "NO JUGAR"

                # Total Alta/Baja según pick
                total_label = "Alta" if pick==away else "Baja"

                report.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "pick": pick,
                    "confidence": round(confidence, 2),
                    "total": total,
                    "total_label": total_label,
                    "handicap": handicap,
                    "level": level,
                    "recommended": recommended
                })
            except:
                continue

    return report
