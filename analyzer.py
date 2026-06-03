print("🔥 ANALYZER VERSION V5.7 PITCHER INTELLIGENCE")

def run(games):

    print("🏦 SHARP MONEY V5.7 PITCHER ENGINE START")

    if not games:
        print("❌ No games found")
        return []

    report = []

    for game in games:

        try:

            home = game["home"]
            away = game["away"]
            odds = game["odds"]

            pitchers = game.get("pitchers", {})

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
            # STEAM (base estructural)
            # =========================
            steam_value = game.get("movement", 0)

            if steam_value >= 3:
                steam = "🔥 SHARP MONEY IN"
            elif steam_value <= -3:
                steam = "❄️ REVERSE LINE"
            else:
                steam = "⚪ NEUTRAL"

            # =========================
            # PITCHERS (REAL READY)
            # =========================
            def get_pitcher(team):
                p = pitchers.get(team)
                if not p:
                    return {"name": "TBD", "ERA": "-", "WHIP": "-"}
                return {
                    "name": p.get("name", "TBD"),
                    "ERA": p.get("ERA", "-"),
                    "WHIP": p.get("WHIP", "-")
                }

            home_p = get_pitcher(home)
            away_p = get_pitcher(away)

            pitcher_info = (
                f"{away_p['name']} (ERA: {away_p['ERA']}, WHIP: {away_p['WHIP']}) vs "
                f"{home_p['name']} (ERA: {home_p['ERA']}, WHIP: {home_p['WHIP']})"
            )

            # =========================
            # SCORE V5.7 (MEJORADO)
            # =========================
            score = prob + (edge * 0.65)

            # bonus pitcher quality si existe data real
            if away_p["ERA"] != "-" and home_p["ERA"] != "-":
                try:
                    away_era = float(away_p["ERA"])
                    home_era = float(home_p["ERA"])

                    # ventaja al pitcher con menor ERA
                    if (home_era < away_era and pick == home) or (away_era < home_era and pick == away):
                        score += 1.5
                except:
                    pass

            if steam == "🔥 SHARP MONEY IN":
                score += 2
            elif steam == "❄️ REVERSE LINE":
                score -= 2

            # =========================
            # NIVEL V5.7
            # =========================
            if score >= 70:
                level = "🔥 ELITE"
            elif score >= 66:
                level = "✅ STRONG"
            elif score >= 62:
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
                "steam": steam,
                "pitcher": pitcher_info
            })

            print()
            print(f"⚾ {away} vs {home}")
            print(f"🎯 Pick: {pick}")
            print(f"📊 Confianza: {round(prob,2)}%")
            print(f"📈 Edge: {round(edge,2)}%")
            print(f"📡 Steam: {steam}")
            print(f"🧾 Pitchers: {pitcher_info}")
            print(f"🧠 Score: {round(score,2)}")
            print(f"🏷 Nivel: {level}")
            print("----------------")

        except Exception as e:
            print("❌ Game error:", e)
            continue

    report.sort(key=lambda x: x["score"], reverse=True)

    return report
