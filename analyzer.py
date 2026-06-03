def analyze_games(games):

    report = []

    seen = set()

    for g in games:

        home = g["home_team"]
        away = g["away_team"]

        key = f"{away}_vs_{home}"
        if key in seen:
            continue
        seen.add(key)

        hp = g["home_pitcher"]
        ap = g["away_pitcher"]

        def f(x):
            try:
                return float(x)
            except:
                return 4.5

        diff = (f(ap["ERA"]) + f(ap["WHIP"])) - (f(hp["ERA"]) + f(hp["WHIP"]))

        confidence = 50 + diff * 8
        confidence = round(max(40, min(confidence, 78)), 2)

        pick = away if confidence >= 50 else home

        total = 8.5
        if (f(hp["ERA"]) + f(ap["ERA"])) > 9:
            total = 9.5
        elif (f(hp["ERA"]) + f(ap["ERA"])) < 5.5:
            total = 7.5

        handicap = "-1.5" if pick == away else "+1.5"

        if confidence >= 70:
            level = "🔥 ELITE"
        elif confidence >= 62:
            level = "✅ FUERTE"
        elif confidence >= 55:
            level = "⚠️ LEAN"
        else:
            continue  # ❌ FILTRO FUERTE (NO PASAR)

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

    # 🔥 ORDENAR Y LIMITAR
    report = sorted(report, key=lambda x: x["confidence"], reverse=True)[:10]

    return report
