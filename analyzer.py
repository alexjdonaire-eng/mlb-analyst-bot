import requests

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

                # Lógica básica de pick y confianza
                # Aquí puedes reemplazar con tu modelo real
                confidence = round(40 + 30*0.5,2)  # Ejemplo: 55%
                pick = home if confidence < 50 else away
                total = round(7 + 2*(confidence/100),1)  # Total carreras aproximado
                handicap = -1.5 if pick==away else 1.5

                # Nivel según confianza
                if confidence >= 65:
                    level = "🔥 ELITE"
                elif confidence >= 58:
                    level = "✅ FUERTE"
                elif confidence >= 52:
                    level = "⚠️ LEAN"
                else:
                    level = "🚫 PASAR"

                recommended = pick if confidence >= 52 else "NO JUGAR"

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
            except Exception as e:
                continue

    return report
