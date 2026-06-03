import requests

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
        return {
            "ERA": stats.get("era", "-"),
            "WHIP": stats.get("whip", "-")
        }
    except:
        return {"ERA": "-", "WHIP": "-"}


def analyze_games(schedule_data):
    """
    🔥 FIX PRINCIPAL:
    - Ahora SOLO acepta schedule MLB directo
    - evita KeyError 'teams'
    """

    report = []
    seen = set()

    if not schedule_data or "dates" not in schedule_data:
        return []

    for day in schedule_data.get("dates", []):
        for game in day.get("games", []):

            try:
                # ✅ SAFE CHECK
                if "teams" not in game:
                    continue

                home = game["teams"]["home"]["team"]["name"]
                away = game["teams"]["away"]["team"]["name"]

                game_id = f"{away}_vs_{home}"
                if game_id in seen:
                    continue
                seen.add(game_id)

                hp = game["teams"]["home"].get("probablePitcher", {})
                ap = game["teams"]["away"].get("probablePitcher", {})

                home_pitcher = {
                    "name": hp.get("fullName", "TBD"),
                    **fetch_pitcher_stats(hp.get("id"))
                }

                away_pitcher = {
                    "name": ap.get("fullName", "TBD"),
                    **fetch_pitcher_stats(ap.get("id"))
                }

                # 🎯 lógica base mejorada
                confidence = 40

                if home_pitcher["name"] == "TBD" or away_pitcher["name"] == "TBD":
                    confidence -= 5

                pick = away if confidence >= 50 else home

                # ⚾ total simple estable
                try:
                    era_h = float(home_pitcher["ERA"])
                    era_a = float(away_pitcher["ERA"])
                    total = 8.0 + (era_h + era_a) / 10
                except:
                    total = 8.5

                handicap = -1.5 if pick == away else 1.5

                level = (
                    "🔥 ELITE" if confidence >= 70 else
                    "✅ FUERTE" if confidence >= 60 else
                    "⚠️ LEAN" if confidence >= 52 else
                    "🚫 PASAR"
                )

                recommended = pick if confidence >= 52 else "NO JUGAR"

                report.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "pick": pick,
                    "confidence": confidence,
                    "total": round(total, 1),
                    "handicap": handicap,
                    "level": level,
                    "recommended": recommended
                })

            except Exception:
                continue

    return report
