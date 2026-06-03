import requests
import json
from datetime import datetime

FILE = "daily_results.json"

def grade_picks():

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(FILE, "r") as f:
            data = json.load(f)
    except:
        return

    if today not in data:
        return

    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

    try:
        res = requests.get(url, timeout=20)
        games = res.json()
    except:
        return

    for game in games.get("dates", []):

        for g in game.get("games", []):

            status = g["status"]["detailedState"]

            if status != "Final":
                continue

            away = g["teams"]["away"]["team"]["name"]
            home = g["teams"]["home"]["team"]["name"]

            matchup = f"{away} vs {home}"

            away_score = g["teams"]["away"]["score"]
            home_score = g["teams"]["home"]["score"]

            total_runs = away_score + home_score

            for pick in data[today]:

                if pick["game"] != matchup:
                    continue

                result = "PERDIO"

                # GANADOR
                if pick["pick_type"] == "Ganador":

                    winner = home if home_score > away_score else away

                    if winner == pick["pick_value"]:
                        result = "GANO"

                # TOTAL ALTA
                elif pick["pick_type"] == "Total ALTA":

                    if total_runs > float(pick["pick_value"]):
                        result = "GANO"

                # TOTAL BAJA
                elif pick["pick_type"] == "Total BAJA":

                    if total_runs < float(pick["pick_value"]):
                        result = "GANO"

                # HANDICAP
                elif pick["pick_type"] == "Hándicap":

                    team = pick["pick_value"].replace(" -1.5", "")

                    if team == home:

                        if (home_score - away_score) >= 2:
                            result = "GANO"

                    else:

                        if (away_score - home_score) >= 2:
                            result = "GANO"

                pick["result"] = result

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ PICKS CALIFICADOS")
