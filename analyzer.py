def safe_float(x):
    try:
        return float(x)
    except:
        return 4.50


def analyze_games(games_data):

    report = []

    for g in games_data:

        try:
            home = g["home_team"]
            away = g["away_team"]

            hp = g["home_pitcher"]
            ap = g["away_pitcher"]

            home_era = safe_float(hp["ERA"])
            away_era = safe_float(ap["ERA"])
            home_whip = safe_float(hp["WHIP"])
            away_whip = safe_float(ap["WHIP"])

            # =========================
            # MODEL CORE V5.19
            # =========================
            pitcher_diff = (away_era + away_whip) - (home_era + home_whip)

            confidence = 50 + (pitcher_diff * 7.5)

            # límites realistas
            confidence = max(40, min(confidence, 75))

            # pick
            pick = home if confidence < 50 else away

            # totales (más realista)
            combined_era = home_era + away_era

            if combined_era <= 5.5:
                total = 7.5
            elif combined_era <= 7:
                total = 8.5
            else:
                total = 9.5

            # handicap
            handicap = "-1.5" if pick == away else "+1.5"

            # nivel
            if confidence >= 70:
                level = "🔥 ELITE"
            elif confidence >= 62:
                level = "✅ FUERTE"
            elif confidence >= 55:
                level = "⚠️ LEAN"
            else:
                level = "🚫 PASAR"

            # jugada recomendada
            recommended = pick if confidence >= 55 else "NO JUGAR"

            report.append({
                "home_team": home,
                "away_team": away,
                "home_pitcher": hp,
                "away_pitcher": ap,
                "pick": pick,
                "confidence": round(confidence, 2),
                "total": total,
                "handicap": handicap,
                "level": level,
                "recommended": recommended
            })

        except:
            continue

    return report
