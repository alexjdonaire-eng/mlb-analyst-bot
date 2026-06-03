from collector import run as get_games

def run_analyzer():
    games = get_games()
    report = []

    for g in games:
        try:
            home = g.get("home_team")
            away = g.get("away_team")
            hp = g.get("home_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})
            ap = g.get("away_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})

            def safe_float(x):
                try: return float(x)
                except: return 4.50

            home_era = safe_float(hp["ERA"])
            away_era = safe_float(ap["ERA"])
            home_whip = safe_float(hp["WHIP"])
            away_whip = safe_float(ap["WHIP"])

            movement = g.get("movement",0)
            steam = g.get("steam","⚪ NEUTRAL")

            pitcher_diff = (away_era + away_whip) - (home_era + home_whip)
            market_factor = -movement * 0.35
            score = 50 + (pitcher_diff*6.5) + market_factor

            pick = home if score >= 50 else away
            confidence = max(45, min(score,75))
            edge = abs(score-50)

            if confidence >= 64:
                level = "🔥 ELITE"
            elif confidence >= 58:
                level = "✅ STRONG"
            else:
                level = "⚠️ LEAN"

            report.append({
                "home_team": home,
                "away_team": away,
                "pick": pick,
                "confidence": round(confidence,2),
                "edge": round(edge,2),
                "steam": steam,
                "market_move": round(movement,2),
                "score": round(score,2),
                "level": level,
                "home_pitcher": hp,
                "away_pitcher": ap
            })
        except:
            continue

    # Ordenar Top 5 Picks
    top5 = sorted(report, key=lambda x: x["confidence"], reverse=True)[:5]

    return report, top5
