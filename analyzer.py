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

        home_odds = odds.get(home)
        away_odds = odds.get(away)

        if not home_odds or not away_odds:
            continue

        # =========================
        # PROBABILIDADES
        # =========================
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds

        total = home_prob + away_prob

        home_prob = (home_prob / total) * 100
        away_prob = (away_prob / total) * 100

        if home_prob > away_prob:
            pick = home
            prob = home_prob
        else:
            pick = away
            prob = away_prob

        edge = prob - 50

        # =========================
        # NIVEL
        # =========================
        if prob >= 62:
            level = "🔥 ELITE"
        elif prob >= 59:
            level = "✅ STRONG"
        elif prob >= 57:
            level = "⚠️ LEAN"
        else:
            continue

        # =========================
        # STEAM (opcional si existe)
        # =========================
        steam = game.get("movement", 0)

        steam_signal = "⚪ NEUTRAL"

        if steam > 3:
            steam_signal = "🔥 SHARP MONEY IN"
        elif steam < -3:
            steam_signal = "❄️ REVERSE LINE"

        # =========================
        # FULL VISIBILITY MODE
        # =========================
        # SOLO eliminar basura real
        if prob < 57:
            continue

        # =========================
        # LOG OUTPUT
        # =========================
        print()
        print(f"⚾ {away} vs {home}")
        print(f"🎯 Pick: {pick}")
        print(f"📊 Confianza: {round(prob,2)}%")
        print(f"📈 Edge: {round(edge,2)}%")
        print(f"📊 Steam: {steam_signal}")
        print(f"🏷 Nivel: {level}")
        print("----------------")

        report.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "probability": round(prob, 2),
            "edge": round(edge, 2),
            "level": level,
            "steam": steam_signal
        })

    return report
