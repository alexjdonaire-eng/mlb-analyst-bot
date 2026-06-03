def run_analyzer():

    print("🏦 SHARP MONEY V5.10 ANALYZER START")

    # =========================
    # IMPORTANTE:
    # Este analyzer espera que el collector ya traiga:
    # - home_team
    # - away_team
    # - pitcher_home
    # - pitcher_away
    # - movement
    # - steam
    # =========================

    try:
        from collector import run as get_games
        games = get_games()
    except Exception as e:
        print(f"❌ Collector error: {e}")
        return []

    report = []

    for g in games:

        try:
            home = g.get("home_team")
            away = g.get("away_team")

            # =========================
            # PITCHERS
            # =========================
            hp = g.get("pitcher_home", {"name":"TBD","ERA":"-","WHIP":"-"})
            ap = g.get("pitcher_away", {"name":"TBD","ERA":"-","WHIP":"-"})

            def safe_float(x):
                try:
                    return float(x)
                except:
                    return 4.50

            home_era = safe_float(hp["ERA"])
            away_era = safe_float(ap["ERA"])
            home_whip = safe_float(hp["WHIP"])
            away_whip = safe_float(ap["WHIP"])

            # =========================
            # MARKET
            # =========================
            movement = g.get("movement", 0)

            # =========================
            # MODEL CORE V5.10
            # =========================
            pitcher_diff = (away_era + away_whip) - (home_era + home_whip)

            market_factor = -movement * 0.35

            score = 50 + (pitcher_diff * 6.5) + market_factor

            # =========================
            # PICK LOGIC
            # =========================
            if score >= 55:
                pick = home
            else:
                pick = away

            confidence = max(45, min(score, 75))
            edge = abs(score - 50)

            # =========================
            # LEVEL SYSTEM
            # =========================
            if confidence >= 64:
                level = "🔥 ELITE"
            elif confidence >= 58:
                level = "✅ STRONG"
            else:
                level = "⚠️ LEAN"

            # =========================
            # STEAM
            # =========================
            steam = g.get("steam", "⚪ NEUTRAL")

            # =========================
            # OUTPUT OBJECT
            # =========================
            report.append({
                "home_team": home,
                "away_team": away,
                "pick": pick,
                "confidence": round(confidence, 2),
                "edge": round(edge, 2),
                "steam": steam,
                "market_move": movement,
                "score": round(score, 2),
                "level": level,

                "home_pitcher": hp,
                "away_pitcher": ap
            })

        except Exception as e:
            print(f"❌ Game error: {e}")

    print(f"📊 Games loaded: {len(report)}")

    return report
