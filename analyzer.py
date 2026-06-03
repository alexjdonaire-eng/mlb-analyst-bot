def run():
    """
    🧠 ANALYZER V5.15
    Espera que collector.py ya traiga:
    - home_team, away_team
    - home_pitcher, away_pitcher
    - movement
    - steam
    """
    try:
        from collector import run as get_games
        games = get_games()
    except Exception as e:
        print(f"❌ Error al ejecutar collector: {e}")
        return []

    report = []

    for g in games:
        try:
            home = g.get("home_team")
            away = g.get("away_team")

            hp = g.get("home_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})
            ap = g.get("away_pitcher", {"name":"TBD","ERA":"-","WHIP":"-"})

            def safe_float(x):
                try:
                    return float(x)
                except:
                    return 4.50

            home_era = safe_float(hp["ERA"])
            away_era = safe_float(ap["ERA"])
            home_whip = safe_float(hp["WHIP"])
            away_whip = safe_float(ap["WHIP"])

            movement = g.get("movement", 0)

            # =========================
            # Score base
            # =========================
            pitcher_diff = (away_era + away_whip) - (home_era + home_whip)
            market_factor = -movement * 0.35
            score = 50 + (pitcher_diff * 6.5) + market_factor

            # =========================
            # Pick ganador
            # =========================
            if score >= 55:
                pick = home
            else:
                pick = away

            confidence = max(45, min(score, 75))
            edge = abs(score - 50)

            # =========================
            # Nivel
            # =========================
            if confidence >= 64:
                level = "🔥 ELITE"
            elif confidence >= 58:
                level = "✅ FUERTE"
            else:
                level = "⚠️ LEAN"

            report.append({
                "home_team": home,
                "away_team": away,
                "home_pitcher": hp,
                "away_pitcher": ap,
                "pick": pick,
                "confidence": round(confidence,2),
                "edge": round(edge,2),
                "level": level,
                "steam": g.get("steam","⚪ NEUTRAL"),
                "market_move": movement,
                "score": round(score,2)
            })

        except Exception as e:
            print(f"❌ Error procesando juego {home} vs {away}: {e}")

    return report
