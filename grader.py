import requests
import os
import json
from datetime import datetime
from tracker import update_pick

# URL para obtener resultados MLB
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=decisions,probablePitcher,linescore"

def fetch_results():
    """Trae los resultados de los juegos de hoy"""
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []

    results = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            try:
                home = g["teams"]["home"]["team"]["name"]
                away = g["teams"]["away"]["team"]["name"]

                # Chequea si el juego terminó
                status = g.get("status", {}).get("detailedState", "")
                if status != "Final":
                    continue

                # Score
                home_score = g["teams"]["home"]["score"]
                away_score = g["teams"]["away"]["score"]

                results.append({
                    "game": f"{away} vs {home}",
                    "home_score": home_score,
                    "away_score": away_score
                })
            except:
                continue

    return results

def grade_picks():
    """Actualiza daily_results.json marcando cada pick como GANO o PERDIÓ"""
    results = fetch_results()
    today = datetime.now().strftime("%Y-%m-%d")

    if not results:
        print("No hay resultados finales hoy aún.")
        return

    # Carga el registro
    try:
        with open("daily_results.json", "r") as f:
            data = json.load(f)
    except:
        print("No hay registro diario.")
        return

    if today not in data:
        print("No hay picks para hoy.")
        return

    for pick in data[today]:
        game_name = pick["game"]
        pick_text = pick["pick"]

        # Buscar el resultado real
        game_result = next((r for r in results if r["game"] == game_name), None)
        if not game_result:
            continue

        home_score = game_result["home_score"]
        away_score = game_result["away_score"]

        # Revisar tipo de pick
        pick_type = pick_text.split()[0]
        pick_value = " ".join(pick_text.split()[1:])

        # Ganador ML
        if pick_type.lower() == "ganador":
            winner = pick_value
            actual_winner = game_name.split(" vs ")[1] if home_score > away_score else game_name.split(" vs ")[0]
            result = "GANO" if winner == actual_winner else "PERDIO"

        # Total ALTA/BAJA
        elif pick_type.lower() == "total":
            total_line = float(pick_value)
            if "ALTA" in pick_text.upper():
                result = "GANO" if (home_score + away_score) > total_line else "PERDIO"
            else:
                result = "GANO" if (home_score + away_score) < total_line else "PERDIO"

        # Hándicap (simple: -1.5)
        elif pick_type.lower() == "hándicap":
            team = pick_value.split()[0]
            margin = 1.5
            actual_diff = (home_score - away_score) if team == game_name.split(" vs ")[1] else (away_score - home_score)
            result = "GANO" if actual_diff > margin else "PERDIO"

        else:
            result = "PENDIENTE"

        # Actualiza el pick
        update_pick(game_name, result)

    print("✅ Picks calificados correctamente.")
