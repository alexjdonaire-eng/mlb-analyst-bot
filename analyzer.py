def run_analyzer():
    from collector import run as get_games
    games = get_games()
    report = []

    def safe_float(x):
        try:
            return float(x)
        except:
            return 4.5

    for g in games:
        try:
            home = g["home_team"]
            away = g["away_team"]
            hp = g["home_pitcher"]
            ap = g["away_pitcher"]

            home_era = safe_float(hp["ERA"])
            away_era = safe_float(ap["ERA"])
            home_whip = safe_float(hp["WHIP"])
            away_whip = safe_float(ap["WHIP"])

            pitcher_edge = (away_era + away_whip) - (home_era + home_whip)
            market_factor = g.get("market_move",0) * 0.25

            score = 50 + pitcher_edge*5 + market_factor
            score = min(max(score,40),72)

            if score >= 55:
                pick = home
            else:
                pick = away

            # Totales y hándicap simulados o desde Odds API
            totals = g.get("totals", [{"point":8.5}])
            spreads = g.get("spread", [{"point":1.5}])

            confidence = round(score,2)
            if confidence>=64:
                level="🔥 ELITE"
            elif confidence>=58:
                level="✅ FUERTE"
            else:
                level="⚠️ LEAN"

            report.append({
                "home_team": home,
                "away_team": away,
                "home_pitcher": hp,
                "away_pitcher": ap,
                "pick": pick,
                "totals": totals[0]["point"],
                "handicap": spreads[0]["point"],
                "confidence": confidence,
                "level": level
            })
        except Exception as e:
            print(f"❌ Error procesando juego: {e}")

    print(f"📊 Analyzer loaded: {len(report)} games")
    return report
