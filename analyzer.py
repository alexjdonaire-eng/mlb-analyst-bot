def safe_float(x):
    try:
        return float(x)
    except:
        return 4.5


def analyze_games(games_data):

    report = []

    for g in games_data:

        home = g["home_team"]
        away = g["away_team"]

        hp = g["home_pitcher"]
        ap = g["away_pitcher"]

        home_era = safe_float(hp["ERA"])
        away_era = safe_float(ap["ERA"])
        home_whip = safe_float(hp["WHIP"])
        away_whip = safe_float(ap["WHIP"])

        # =========================
        # CORE V6 MODEL
        # =========================
        diff = (away_era + away_whip) - (home_era + home_whip)

        confidence = 50 + diff * 8.2
        confidence = max(40, min(confidence, 78))

        pick = home if confidence < 50 else away

        # totales más agresivos
        total = 7.5
        if (home_era + away_era) > 8:
            total = 9.0
        elif (home_era + away_era) < 5.5:
            total = 7.0

        handicap = "-1.5" if pick == away else "+1.5"

        # nivel
        if confidence >= 70:
            level = "🔥 ELITE"
        elif confidence >= 62:
            level = "✅ FUERTE"
        elif confidence >= 55:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASS"

        # SOLO VALUE BETS
        if confidence < 55:
            continue

        report.append({
            "home_team": home,
            "away_team": away,
            "pick": pick,
            "confidence": round(confidence, 2),
            "total": total,
            "handicap": handicap,
            "level": level
        })

    return report
