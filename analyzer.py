print("🔥 ANALYZER VERSION V5.4")

def run(games):
    print("🏦 SHARP MONEY V5.4 FILTER ENGINE START")

    if not games:
        print("❌ No games found")
        return []

    report = []

    for game in games:
        home = game["home"]
        away = game["away"]
        odds = game["odds"]
        steam = game.get("steam", {home: "⚪ NEUTRAL", away: "⚪ NEUTRAL"})
        pitchers = game.get("pitchers", {})

        home_odds = odds.get(home)
        away_odds = odds.get(away)

        if not home_odds or not away_odds:
            continue

        # Probabilidades implícitas
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds
        total = home_prob + away_prob
        home_prob = (home_prob / total) * 100
        away_prob = (away_prob / total) * 100

        # Pick principal
        if home_prob > away_prob:
            pick = home
            prob = home_prob
        else:
            pick = away
            prob = away_prob

        edge = prob - 50

        # Determinar nivel
        if prob >= 62:
            level = "🔥 ELITE"
        elif prob >= 59:
            level = "✅ STRONG"
        elif prob >= 57:
            level = "⚠️ LEAN"
        else:
            continue

        # Filtrado avanzado
        # Lean solo pasa si hay steam positivo
        pick_steam = steam.get(pick, "⚪ NEUTRAL")
        if level == "⚠️ LEAN" and "🔥" not in pick_steam:
            continue

        # Build reporte
        pitcher_info = ""
        if pick in pitchers:
            pitcher_info = f"\n🎳 Pitcher: {pitchers[pick]['name']} (ERA: {pitchers[pick]['era']})"

        report.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "probability": round(prob, 2),
            "edge": round(edge, 2),
            "level": level,
            "steam": pick_steam,
            "pitcher": pitcher_info
        })

        # Log
        print()
        print(f"⚾ {away} vs {home}")
        print(f"🎯 Pick: {pick}")
        print(f"📊 Confianza: {round(prob,2)}%")
        print(f"📈 Edge: {round(edge,2)}%")
        print(f"📊 Steam: {pick_steam}")
        print(f"🏷 Nivel: {level}")
        if pitcher_info:
            print(pitcher_info)
        print("----------------")

    return report
