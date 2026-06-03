# analyzer.py
def analyze_games(games):
    analyzed = []
    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        
        # Simulación de predicciones (reemplaza con tu lógica real)
        winner = {"team": home, "prob": 55}  # ejemplo
        total = {"line": 8.5, "prob": 60, "type": "Alta"}
        handicap = {"line": f"{home} -1.5", "prob": 58}
        
        # Crear lista de picks con tipo
        picks = [
            {"type": "Ganador", "value": winner["team"], "prob": winner["prob"]},
            {"type": f"Total {total['type']}", "value": f"{total['line']}", "prob": total["prob"]},
            {"type": "Hándicap", "value": handicap["line"], "prob": handicap["prob"]}
        ]
        
        # Mejor pick del juego según probabilidad
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
