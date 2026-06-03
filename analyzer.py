import requests

# ===========================================
# FUNCIONES DE APOYO
# ===========================================

def pitcher_score(era, whip):
    """Convierte ERA y WHIP en un score de pitcher"""
    try:
        era = float(era)
        whip = float(whip)
        score = 100 - (era * 10 + whip * 15)
        return max(score, 1)
    except:
        return 50

def implied_probability(odds):
    """Convierte odds tipo decimal a % implícito"""
    try:
        return round(100 / odds, 2)
    except:
        return 50

def projected_total_runs(home_era, away_era):
    """Proyección simple de carreras usando ERA"""
    try:
        return float(home_era) + float(away_era)
    except:
        return 8.5

def total_confidence(projected_runs, total_line):
    """Confianza de Total Alta/Baja"""
    diff = abs(projected_runs - total_line)
    return min(80, round(55 + diff * 5))

def runline_confidence(home_prob, away_prob):
    margin = abs(home_prob - away_prob)
    if margin > 20:
        return 70
    elif margin > 10:
        return 62
    else:
        return 55

# ===========================================
# ANALYZER
# ===========================================

def analyze_games(games, odds_data=None):
    """
    games = lista de juegos con pitchers y equipos
    odds_data = dict opcional con moneylines y totales de cada juego
    """
    analyzed = []
    all_picks = []

    for g in games:

        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})

        # =================================
        # SCORES DE PITCHERS
        # =================================
        home_score = pitcher_score(home_pitcher["ERA"], home_pitcher["WHIP"])
        away_score = pitcher_score(away_pitcher["ERA"], away_pitcher["WHIP"])
        total_score = home_score + away_score

        home_prob = round(home_score / total_score * 100)
        away_prob = round(away_score / total_score * 100)

        # =================================
        # ODDS (si hay datos del mercado)
        # =================================
        if odds_data:
            game_key = f"{away} vs {home}"
            ml_home = odds_data.get(game_key, {}).get("ml_home", 2.0)
            ml_away = odds_data.get(game_key, {}).get("ml_away", 2.0)
            total_line = odds_data.get(game_key, {}).get("total", 8.5)

            home_prob = round(home_prob * 0.6 + implied_probability(ml_home) * 0.4)
            away_prob = round(away_prob * 0.6 + implied_probability(ml_away) * 0.4)
        else:
            total_line = 8.5

        # =================================
        # GANADOR
        # =================================
        if home_prob > away_prob:
            winner = home
            winner_prob = home_prob
        else:
            winner = away
            winner_prob = away_prob

        # =================================
        # TOTAL ALTA / BAJA
        # =================================
        projected_runs = projected_total_runs(home_pitcher["ERA"], away_pitcher["ERA"])

        if projected_runs >= total_line:
            total_type = "ALTA"
        else:
            total_type = "BAJA"

        total_prob = total_confidence(projected_runs, total_line)

        # =================================
        # HÁNDICAP
        # =================================
        runline_pick = f"{winner} -1.5"
        runline_prob = runline_confidence(home_prob, away_prob)

        # =================================
        # ELEGIR MEJOR PICK
        # =================================
        options = [
            {"type": "Ganador", "pick": winner, "confidence": winner_prob},
            {"type": f"Total {total_type}", "pick": f"{total_line}", "confidence": total_prob},
            {"type": "Hándicap", "pick": runline_pick, "confidence": runline_prob}
        ]

        best_pick = max(options, key=lambda x: x["confidence"])
        confidence = best_pick["confidence"]

        if confidence >= 75:
            level = "🔥 ELITE"
        elif confidence >= 65:
            level = "✅ FUERTE"
        elif confidence >= 55:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        # =================================
        # MENSAJE POR JUEGO
        # =================================
        game_message = f"""
⚾ {away} vs {home}

🧾 Lanzadores
{away}: {away_pitcher['name']} (ERA {away_pitcher['ERA']} | WHIP {away_pitcher['WHIP']})
{home}: {home_pitcher['name']} (ERA {home_pitcher['ERA']} | WHIP {home_pitcher['WHIP']})

🎯 Ganador: {winner} ({winner_prob}%)
⚾ Total: {total_type} {total_line} ({total_prob}%)
⚾ Hándicap: {runline_pick} ({runline_prob}%)

📊 Confianza: {confidence}%
🏷 Nivel: {level}
💎 Jugada: {best_pick['type']} → {best_pick['pick']} ({confidence}%)
"""

        analyzed.append({
            "message": game_message,
            "top_pick": {
                "game": f"{away} vs {home}",
                "type": best_pick["type"],
                "pick": best_pick["pick"],
                "confidence": confidence,
                "level": level
            }
        })

        all_picks.append(analyzed[-1]["top_pick"])

    # =================================
    # TOP 5 PICKS DEL DÍA
    # =================================
    all_picks.sort(key=lambda x: x["confidence"], reverse=True)
    top5 = all_picks[:5]

    top_message = "\n🔥 TOP 5 PICKS DEL DÍA\n"
    for i, pick in enumerate(top5, start=1):
        top_message += f"""
{i}️⃣ {pick['type']}
{pick['game']}
➡️ {pick['pick']} ({pick['confidence']}%)
{pick['level']}
"""

    return analyzed, top_message
