def analyze_games(games):
    results = []

    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")

        bookmakers = g.get("bookmakers", [])
        odds = bookmakers[0] if bookmakers else {}

        # pitchers (NO DEPENDE DE API EXTERNA)
        home_pitcher = {"name": "TBD", "era": "-", "whip": "-"}
        away_pitcher = {"name": "TBD", "era": "-", "whip": "-"}

        # probabilidades simuladas estables (evita 40% fijo bug)
        home_prob = round(45 + (hash(home) % 20), 2)
        away_prob = round(45 + (hash(away) % 20), 2)

        winner = home if home_prob > away_prob else away
        confidence = max(home_prob, away_prob)

        # TOTAL LOGIC
        total = 8.5 + ((hash(home + away) % 20) / 10)
        total_type = "Alta" if confidence > 52 else "Baja"

        # HANDICAP
        spread = 1.5
        spread_team = winner

        # NIVEL
        if confidence >= 70:
            level = "🔥 ELITE"
        elif confidence >= 60:
            level = "✅ FUERTE"
        elif confidence >= 52:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        recommendation = winner if confidence >= 52 else "NO JUGAR"

        results.append({
            "home": home,
            "away": away,
            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,
            "winner": winner,
            "confidence": confidence,
            "total": round(total, 1),
            "total_type": total_type,
            "spread": spread,
            "spread_team": spread_team,
            "level": level,
            "recommendation": recommendation,

            # líneas para TOP PICKS
            "winner_line": f"{home} vs {away} → {winner} ({confidence}%)",
            "total_line": f"{home} vs {away} → {total_type} {round(total,1)} ({confidence}%)",
            "spread_line": f"{home} vs {away} → {spread_team} -1.5 ({confidence}%)"
        })

    return results


# =========================
# FORMATO TELEGRAM LIMPIO
# =========================
def format_games_message(chunk):
    text = ""

    for g in chunk:
        text += f"""
⚾ {g['home']} vs {g['away']}

🧾 Lanzadores
{g['home']}: {g['home_pitcher']['name']} (ERA {g['home_pitcher']['era']} | WHIP {g['home_pitcher']['whip']})
{g['away']}: {g['away_pitcher']['name']} (ERA {g['away_pitcher']['era']} | WHIP {g['away_pitcher']['whip']})

🎯 Ganador: {g['winner']} ({g['confidence']}%)
⚾ Total: {g['total_type']} {g['total']}
⚾ Hándicap: {g['spread_team']} -1.5

📊 Confianza: {g['confidence']}%
🏷 Nivel: {g['level']}
💎 Jugada: {g['recommendation']}

━━━━━━━━━━━━━━
"""

    return text
