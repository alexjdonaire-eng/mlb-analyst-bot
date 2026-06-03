def analyze_games(raw_games):
    analyzed = []
    for g in raw_games:
        # Prevenir KeyError
        home_team = g.get('home_team', 'TBD')
        away_team = g.get('away_team', 'TBD')
        hp = g.get('home_pitcher', {'name': 'TBD', 'era': '-', 'whip': '-'})
        ap = g.get('away_pitcher', {'name': 'TBD', 'era': '-', 'whip': '-'})

        # Probabilidades simuladas para demo (puedes reemplazar con tu lógica)
        winner_pct = round(g.get('winner_prob', 40.0), 2)
        total = round(g.get('total', 9.0), 1)
        total_type = g.get('total_type', 'Alta')
        total_pct = round(g.get('total_prob', 40.0), 2)
        handicap = g.get('handicap_value', 1.5)
        handicap_team = g.get('handicap_team', away_team)
        handicap_pct = round(g.get('handicap_prob', 40.0), 2)
        confidence = round((winner_pct + total_pct + handicap_pct)/3, 2)

        # Definir nivel
        if confidence >= 75:
            level = "ELITE 🔥"
            recommendation = f"{home_team} gana" if winner_pct > 50 else f"{away_team} gana"
        elif confidence >= 60:
            level = "FUERTE ✅"
            recommendation = f"{home_team} gana" if winner_pct > 50 else f"{away_team} gana"
        elif confidence >= 50:
            level = "LEAN ⚠️"
            recommendation = f"{home_team} gana" if winner_pct > 50 else f"{away_team} gana"
        else:
            level = "PASAR 🚫"
            recommendation = "NO JUGAR"

        analyzed.append({
            "home_team": home_team,
            "away_team": away_team,
            "home_pitcher": hp,
            "away_pitcher": ap,
            "winner": home_team if winner_pct > 50 else away_team,
            "winner_pct": winner_pct,
            "total": total,
            "total_type": total_type,
            "total_pct": total_pct,
            "handicap": handicap,
            "handicap_team": handicap_team,
            "handicap_pct": handicap_pct,
            "confidence": confidence,
            "level": level,
            "recommendation": recommendation
        })
    return analyzed
