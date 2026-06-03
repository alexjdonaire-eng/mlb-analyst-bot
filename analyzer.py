def analyze_games(games):

    report = []

    def f(x):
        try:
            return float(x)
        except:
            return 4.5

    for g in games:

        home = g["home_team"]
        away = g["away_team"]

        hp = g["home_pitcher"]
        ap = g["away_pitcher"]

        home_score = f(hp["ERA"]) + f(hp["WHIP"])
        away_score = f(ap["ERA"]) + f(ap["WHIP"])

        diff = away_score - home_score

        confidence = 50 + diff * 7.5
        confidence = round(max(35, min(confidence, 80)), 2)

        pick = away if confidence >= 50 else home

        total = 8.5
        if home_score + away_score > 9:
            total = 9.5
        elif home_score + away_score < 6:
            total = 7.5

        handicap = "-1.5" if pick == away else "+1.5"

        # NIVEL SYSTEM PRO
        if confidence >= 72:
            level = "🔥 ELITE"
        elif confidence >= 62:
            level = "✅ FUERTE"
        elif confidence >= 52:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        # no eliminar juegos, TODOS entran
        report.append({
            "home_team": home,
            "away_team": away,
            "home_pitcher": hp,
            "away_pitcher": ap,
            "pick": pick,
            "confidence": confidence,
            "total": total,
            "handicap": handicap,
            "level": level
        })

    # orden por mejor valor
    report = sorted(report, key=lambda x: x["confidence"], reverse=True)

    return report
