def run(games):

    report = []

    print("🏦 SHARP MONEY V5.9 ANALYZER START")

    for g in games:

        try:
            away = g["away_team"]
            home = g["home_team"]

            # =========================
            # PITCHERS
            # =========================
            home_p = g["pitcher_home"]
            away_p = g["pitcher_away"]

            home_era = float(home_p["ERA"]) if home_p["ERA"] != "-" else 4.50
            away_era = float(away_p["ERA"]) if away_p["ERA"] != "-" else 4.50

            home_whip = float(home_p["WHIP"]) if home_p["WHIP"] != "-" else 1.30
            away_whip = float(away_p["WHIP"]) if away_p["WHIP"] != "-" else 1.30

            # =========================
            # MARKET MOVEMENT
            # =========================
            movement = g.get("movement", 0)

            # =========================
            # BASE MODEL (simple but effective)
            # =========================
            pitcher_adv = (away_era + away_whip) - (home_era + home_whip)

            market_bias = -movement * 0.3

            score = 50 + (pitcher_adv * 6) + market_bias

            # =========================
            # PICK LOGIC
            # =========================
            if score >= 55:
                pick = home
            else:
                pick = away

            # =========================
            # PROBABILITY (soft sigmoid style)
            # =========================
            probability = round(min(max(score, 45), 75), 2)

            edge = round(abs(score - 50), 2)

            # =========================
            # LEVEL
            # =========================
            if probability >= 64:
                level = "🔥 ELITE"
            elif probability >= 58:
                level = "✅ STRONG"
            else:
                level = "⚠️ LEAN"

            # =========================
            # STEAM
            # =========================
            steam = g.get("steam", "⚪ NEUTRAL")

            # =========================
            # BUILD REPORT ITEM
            # =========================
            report.append({
                "game": g["game"],
                "pick": pick,
                "probability": probability,
                "edge": edge,
                "level": level,
                "steam": steam,
                "movement": movement,

                "pitcher": (
                    f"{home_p['name']} (ERA {home_p['ERA']}, WHIP {home_p['WHIP']})"
                    f" vs "
                    f"{away_p['name']} (ERA {away_p['ERA']}, WHIP {away_p['WHIP']})"
                ),

                "score": round(score, 2)
            })

        except Exception as e:
            print("❌ Game error:", e)

    print("📊 Games loaded:", len(report))

    return report
