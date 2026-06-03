import requests
import time

# ---------- FETCH PITCHER STATS ----------
def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"ERA": "-", "WHIP": "-"}
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        res = requests.get(url, timeout=15)
        data = res.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {"ERA": "-", "WHIP": "-"}
        stat = splits[0].get("stat", {})
        return {"ERA": stat.get("era", "-"), "WHIP": stat.get("whip", "-")}
    except:
        return {"ERA": "-", "WHIP": "-"}

# ---------- ANALYZE GAMES ----------
def analyze_games(games):
    analyzed = []

    for game in games:
        # Pitchers reales con fallback
        hp = game["teams"]["home"].get("probablePitcher") or {}
        ap = game["teams"]["away"].get("probablePitcher") or {}

        home_id = hp.get("id")
        away_id = ap.get("id")

        home_pitcher = {"name": hp.get("fullName", "TBD")}
        home_pitcher.update(fetch_pitcher_stats(home_id))
        time.sleep(0.2)

        away_pitcher = {"name": ap.get("fullName", "TBD")}
        away_pitcher.update(fetch_pitcher_stats(away_id))
        time.sleep(0.2)

        # Confianza simulada por ejemplo
        confidence = max(game.get("winner_pct", 0), game.get("total_pct",0), game.get("handicap_pct",0))

        # Determinar nivel
        if confidence >= 70:
            level = "ELITE 🔥"
        elif confidence >= 60:
            level = "FUERTE ✅"
        elif confidence >= 50:
            level = "LEAN ⚠️"
        else:
            level = "PASAR 🚫"

        # Determinar jugada recomendada
        if confidence >= 60:
            recommended = f"{game.get('winner','?')} gana"
        else:
            recommended = "NO JUGAR"

        analyzed.append({
            "match": f"{game['home']} vs {game['away']}",
            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,
            "winner": game.get("winner","?"),
            "winner_pct": game.get("winner_pct", 0),
            "total": game.get("total_value", 0),
            "total_type": game.get("total_type","Alta/Baja"),
            "total_pct": game.get("total_pct",0),
            "handicap": game.get("handicap_value",0),
            "handicap_team": game.get("handicap_team",""),
            "handicap_pct": game.get("handicap_pct",0),
            "confidence": round(confidence,2),
            "level": level,
            "recommended": recommended
        })

    return analyzed

# ---------- TOP PICKS ----------
def top_picks(analyzed):
    winners = sorted(analyzed, key=lambda x: x["winner_pct"], reverse=True)
    totals = sorted(analyzed, key=lambda x: x["total_pct"], reverse=True)
    handicaps = sorted(analyzed, key=lambda x: x["handicap_pct"], reverse=True)

    top5_winners = winners[:5]
    top5_totals = totals[:5]
    top5_handicaps = handicaps[:5]

    return top5_winners, top5_totals, top5_handicaps
