def analyze_games(games):
    analyzed = []
    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "era": "-", "whip": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "era": "-", "whip": "-"})
        
        # Simulación de predicciones (para reemplazar por tu lógica)
        winner = {"team": home, "prob": 55}  # ejemplo
        total = {"line": 8.5, "prob": 60, "type": "Alta"}
        handicap = {"line": f"{home} -1.5", "prob": 58}
        
        # Determinar mejor pick del juego según probabilidad
        picks = [
            {"type": "Ganador", "value": winner["team"], "prob": winner["prob"]},
            {"type": "Total Alta" if total["type"]=="Alta" else "Total Baja", "value": f"{total['line']}", "prob": total["prob"]},
            {"type": "Hándicap", "value": handicap["line"], "prob": handicap["prob"]}
        ]
        best_pick = max(picks, key=lambda x: x["prob"])
        
        level = "✅ FUERTE" if best_pick["prob"] >= 65 else ("⚠️ LEAN" if best_pick["prob"] >= 50 else "🚫 PASAR")
        confidence = best_pick["prob"]
        
        analyzed.append({
            "home": home,
            "away": away,
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
