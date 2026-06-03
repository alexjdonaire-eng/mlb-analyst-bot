print("🔥 ANALYZER VERSION NUEVA")

def run(games):

    print("🏦 SHARP MONEY V4 INSTITUTIONAL")

    if not games:
        print("❌ No games found")
        return []

    report = []

    for game in games:

        home = game["home"]
        away = game["away"]
        odds = game["odds"]

        home_odds = odds.get(home)
        away_odds = odds.get(away)

        if not home_odds or not away_odds:
            continue

        home_prob = 1 / home_odds
        away_prob = 1 / away_odds

        total = home_prob + away_prob

        home_prob = (home_prob / total) * 100
        away_prob = (away_prob / total) * 100

        if home_prob > away_prob:
            pick = home
            prob = home_prob
        else:
            pick = away
            prob = away_prob

        edge = prob - 50

        if edge < 5:
            continue

        print()
        print(f"⚾ {away} vs {home}")
        print(f"🎯 Pick: {pick}")
        print(f"📊 Prob: {round(prob,2)}%")
        print(f"📈 Edge: {round(edge,2)}%")
        print("----------------")

        report.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "probability": round(prob, 2),
            "edge": round(edge, 2)
        })

    return report
