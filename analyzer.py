print("🔥 ANALYZER VERSION V5.5")

def run(games):

    print("🏦 SHARP MONEY V5.5 MARKET ENGINE START")

    if not games:
        print("❌ No games found")
        return []

    report = []

    for game in games:

        try:

            home = game["home"]
            away = game["away"]
            odds = game["odds"]

            home_odds = odds.get(home)
            away_odds = odds.get(away)

            if not home_odds or not away_odds:
                continue

            # =========================
            # PROBABILIDAD BASE
            # =========================
            home_prob = 1 / home_odds
            away_prob = 1 / away_odds

            total = home_prob + away_prob

            home_prob = (home_prob / total) * 100
            away_prob = (away_prob / total) * 100

            # =========================
            # PICK
            # =========================
            if home_prob > away_prob:
                pick = home
                prob = home_prob
            else:
                pick = away
                prob = away_prob

            edge = prob - 50

            # =========================
            # STEAM SIMULADO (V5.5 BASE)
            # =========================
            # si algún día tienes movement real, aquí se conecta
            steam_value = game.get("movement", 0)

            if steam_value >= 3:
                steam = "🔥 SHARP MONEY IN"
            elif steam_value <= -3:
                steam = "❄️ REVERSE LINE"
            else:
                steam = "⚪ NEUTRAL"

            # =========================
            # SCORE V5.5 (NUEVO)
            # =========================
            score = prob + (edge * 0.6)

            if steam == "🔥 SHARP MONEY IN":
                score += 2
            elif steam == "❄️ REVERSE LINE":
                score -= 2

            # =========================
            # NIVEL
            # =========================
            if score >= 68:
                level = "🔥 ELITE"
            elif score >= 64:
                level = "✅ STRONG"
            elif score >= 60:
                level = "⚠️ LEAN"
            else:
                continue

            # =========================
            # REPORT
            # =========================
            report.append({
                "game": f"{away} vs {home}",
                "pick": pick,
                "probability": round(prob, 2),
                "edge": round(edge, 2),
                "score": round(score, 2),
                "level": level,
                "steam": steam
            })

            print()
            print(f"⚾ {away} vs {home}")
            print(f"🎯 Pick: {pick}")
            print(f"📊 Confianza: {round(prob,2)}%")
            print(f"📈 Edge: {round(edge,2)}%")
            print(f"📡 Steam: {steam}")
            print(f"🧠 Score: {round(score,2)}")
            print(f"🏷 Nivel: {level}")
            print("----------------")

        except Exception as e:
            print("❌ Game error:", e)
            continue

    # ordenar por score (IMPORTANTE V5.5)
    report.sort(key=lambda x: x["score"], reverse=True)

    return report
