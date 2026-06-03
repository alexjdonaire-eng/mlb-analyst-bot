def run():
    """
    🧠 ANALYZER V5.16
    Espera que collector.py traiga:
    - home_team, away_team
    - home_pitcher, away_pitcher
    - pick, confidence, level
    - total y spread
    """
    try:
        from collector import run as get_games
        games = get_games()
    except Exception as e:
        print(f"❌ Error ejecutando collector: {e}")
        return []

    report = []

    for g in games:
        try:
            report.append({
                "home_team": g["home_team"],
                "away_team": g["away_team"],
                "home_pitcher": g["home_pitcher"],
                "away_pitcher": g["away_pitcher"],
                "pick": g["pick"],
                "confidence": g["confidence"],
                "level": g["level"],
                "total": g.get("total","-"),
                "spread": g.get("spread","-")
            })
        except:
            continue

    return report
