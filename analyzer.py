import requests

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

# ===========================================
# FUNCIONES DE APOYO
# ===========================================

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


# ===========================================
# FUNCIONES DE CÁLCULO
# ===========================================

def pitcher_score(era, whip):
    try:
        era = float(era)
        whip = float(whip)
        score = 100 - (era * 10 + whip * 15)
        return max(score, 1)
    except:
        return 50


def projected_runs(home_era, away_era):
    try:
        return float(home_era) + float(away_era)
    except:
        return 8.5


def total_confidence(projection, total_line):
    diff = abs(projection - total_line)
    confidence = 55 + diff * 5
    return min(round(confidence), 80)


def runline_confidence(home_prob, away_prob):
    margin = abs(home_prob - away_prob)
    if margin >= 20:
        return 70
    elif margin >= 10:
        return 62
    return 55


# ===========================================
# ANALYZER PRINCIPAL
# ===========================================

def analyze_games(games):
    analyzed = []
    all_picks = []

    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})

        # Calcular scores de pitchers
        home_score = pitcher_score(home_pitcher["ERA"], home_pitcher["WHIP"])
        away_score = pitcher_score(away_pitcher["ERA"], away_pitcher["WHIP"])
        score_total = home_score + away_score

        home_prob = round(home_score / score_total * 100)
        away_prob = round(away_score / score_total * 100)

        # Determinar ganador
        if home_prob > away_prob:
            winner = {"team": home, "prob": home_prob}
        else:
            winner = {"team": away, "prob": away_prob}

        # Proyección de Total
        total_line = 8.5
        projection = projected_runs(home_pitcher["ERA"], away_pitcher["ERA"])
        total_type = "ALTA" if projection >= total_line else "BAJA"
        total = {"line": total_line, "prob": total_confidence(projection, total_line), "type": total_type}

        # Hándicap
        handicap = {"line": f"{winner['team']} -1.5", "prob": runline_confidence(home_prob, away_prob)}

        # Determinar mejor pick
        options = [
            {"type": "Ganador", "value": winner["team"], "confidence": winner["prob"]},
            {"type": f"Total {total_type}", "value": f"{total_line}", "confidence": total["prob"]},
            {"type": "Hándicap", "value": handicap["line"], "confidence": handicap["prob"]}
        ]
        best_pick = max(options, key=lambda x: x["confidence"])
        confidence = best_pick["confidence"]

        # Nivel
        if confidence >= 75:
            level = "🔥 ELITE"
        elif confidence >= 65:
            level = "✅ FUERTE"
        elif confidence >= 55:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        # Guardar resultado
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
            "top_pick_game": f"{away} vs {home}",
            "confidence": confidence,
            "level": level
        })

        all_picks.append(analyzed[-1])

    # Construir TOP 5
    all_picks.sort(key=lambda x: x["confidence"], reverse=True)
    top5 = all_picks[:5]
    top_message = "\n🔥 TOP 5 PICKS DEL DÍA\n"
    for i, pick in enumerate(top5, start=1):
        top_message += f"\n{i}️⃣ {pick['top_pick_type']}\n{pick['top_pick_game']}\n➡️ {pick['top_pick_value']} ({pick['confidence']}%)\n{pick['level']}\n"

    return analyzed, top_message
