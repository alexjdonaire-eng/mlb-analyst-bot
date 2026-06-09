import os
import requests

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"

# ===========================================
# FUNCIONES DE APOYO
# ===========================================

def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA": "-", "WHIP": "-"}
    try:
        res = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching",
            timeout=15
        )
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]
        return {"ERA": stats.get("era", "-"), "WHIP": stats.get("whip", "-")}
    except:
        return {"ERA": "-", "WHIP": "-"}


def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    games = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            try:
                home = g["teams"]["home"]["team"]["name"]
                away = g["teams"]["away"]["team"]["name"]

                hp = g["teams"]["home"].get("probablePitcher", {})
                ap = g["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {"name": hp.get("fullName", "TBD"), **fetch_pitcher_stats(hp.get("id"))}
                away_pitcher = {"name": ap.get("fullName", "TBD"), **fetch_pitcher_stats(ap.get("id"))}

                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher
                })
            except:
                continue
    return games

# ===========================================
# FETCH ODDS API
# ===========================================

def fetch_odds():
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")

    if not ODDS_API_KEY:
        print("❌ ODDS_API_KEY NO ENCONTRADA")
        return {}

    url = (
        "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/"
        f"?regions=us&markets=totals,h2h,spreads&apiKey={ODDS_API_KEY}"
    )

    try:
        res = requests.get(url, timeout=20)

        print("ODDS STATUS:", res.status_code)

        data = res.json()

        if not isinstance(data, list):
            print("❌ RESPUESTA ODDS INVÁLIDA:")
            print(data)
            return {}

    except Exception as e:
        print("❌ ERROR ODDS:", e)
        return {}

    odds_data = {}

    for game in data:

        if not isinstance(game, dict):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        if not home or not away:
            continue

        key = f"{away} vs {home}"

        ml_home = None
        ml_away = None
        total = None

        for site in game.get("bookmakers", []):

            for market in site.get("markets", []):

                if market.get("key") == "h2h":

                    for outcome in market.get("outcomes", []):

                        if outcome.get("name") == home:
                            ml_home = outcome.get("price")

                        elif outcome.get("name") == away:
                            ml_away = outcome.get("price")

                elif market.get("key") == "totals":

                    outcomes = market.get("outcomes", [])

                    if outcomes:
                        total = outcomes[0].get("point")

        if ml_home and ml_away and total:
            odds_data[key] = {
                "ml_home": float(ml_home),
                "ml_away": float(ml_away),
                "total": float(total)
            }

    print(f"✅ ODDS CARGADAS: {len(odds_data)}")

    return odds_data
# ===========================================
# FUNCIONES DE CÁLCULO
# ===========================================

def pitcher_score(era, whip):
    try:
        era = float(era)
        whip = float(whip)
        score = 100 - (era * 10 + whip * 15)
        return max(score, 1)
    except:
        return 50

def projected_runs(home_era, away_era):

    try:

        home_era = float(home_era)
        away_era = float(away_era)

        avg_era = (home_era + away_era) / 2

        projected = avg_era * 2.2

        return round(projected, 1)

    except:
        return 8.5

def total_confidence(projection, total_line):
    diff = abs(projection - total_line)
    confidence = 55 + diff * 5
    return min(round(confidence), 80)

def runline_confidence(home_prob, away_prob):
    margin = abs(home_prob - away_prob)
    if margin >= 20:
        return 70
    elif margin >= 10:
        return 62
    return 55

def implied_probability(decimal_odds):
    try:
        return round(100 / decimal_odds, 2)
    except:
        return 50

# ===========================================
# ANALYZER PRINCIPAL CON ODDS
# ===========================================

def analyze_games(games):
    analyzed = []
    all_picks = []

    odds_data = fetch_odds()

    for g in games:
        home = g.get("home_team", "TBD")
        away = g.get("away_team", "TBD")
        home_pitcher = g.get("home_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})
        away_pitcher = g.get("away_pitcher", {"name": "TBD", "ERA": "-", "WHIP": "-"})

        # Scores de pitchers
        home_score = pitcher_score(home_pitcher["ERA"], home_pitcher["WHIP"])
        away_score = pitcher_score(away_pitcher["ERA"], away_pitcher["WHIP"])
        score_total = home_score + away_score
        home_prob = round(home_score / score_total * 100)
        away_prob = round(away_score / score_total * 100)

        # Integrar odds reales si existen
        game_key = f"{away} vs {home}"
        total_line = 8.5
        if game_key in odds_data:
            ml_home = odds_data[game_key]["ml_home"]
            ml_away = odds_data[game_key]["ml_away"]
            total_line = odds_data[game_key]["total"]

            home_prob = round(home_prob * 0.6 + implied_probability(ml_home) * 0.4)
            away_prob = round(away_prob * 0.6 + implied_probability(ml_away) * 0.4)

        # Determinar ganador
        winner = {"team": home if home_prob > away_prob else away,
                  "prob": home_prob if home_prob > away_prob else away_prob}

        # Total ALTA/BAJA
        projection = projected_runs(home_pitcher["ERA"], away_pitcher["ERA"])
        total_type = "ALTA" if projection >= total_line else "BAJA"
        total = {"line": total_line, "prob": total_confidence(projection, total_line), "type": total_type}

        # Hándicap
        handicap = {"line": f"{winner['team']} -1.5", "prob": runline_confidence(home_prob, away_prob)}

        # Mejor pick
        options = [
            {"type": "Ganador", "value": winner["team"], "confidence": winner["prob"]},
            {"type": f"Total {total_type}", "value": f"{total_line}", "confidence": total["prob"]},
            {"type": "Hándicap", "value": handicap["line"], "confidence": handicap["prob"]}
        ]
        best_pick = max(options, key=lambda x: x["confidence"])
        confidence = best_pick["confidence"]

        # Nivel
        if confidence >= 75:
            level = "🔥 ELITE"
        elif confidence >= 65:
            level = "✅ FUERTE"
        elif confidence >= 55:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        analyzed.append({
            "home_team": home,
            "away_team": away,
            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,
            "predicted_winner": winner,
            "predicted_total": total,
            "predicted_handicap": handicap,
            "top_pick_type": best_pick["type"],
            "top_pick_value": best_pick["value"],
            "top_pick_game": f"{away} vs {home}",
            "confidence": confidence,
            "level": level
        })

        all_picks.append(analyzed[-1])

    # Construir TOP 5
    all_picks.sort(key=lambda x: x["confidence"], reverse=True)
    top5 = all_picks[:5]
    top_message = "\n🔥 TOP 5 PICKS DEL DÍA\n"
    for i, pick in enumerate(top5, start=1):
        top_message += f"\n{i}️⃣ {pick['top_pick_type']}\n{pick['top_pick_game']}\n➡️ {pick['top_pick_value']} ({pick['confidence']}%)\n{pick['level']}\n"

    return analyzed, top_message
