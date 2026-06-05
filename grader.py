import requests
import json
import os

FILE = "daily_results.json"

def grade_picks():

    print("=== GRADER START ===")

    print("Archivo existe:", os.path.exists(FILE))

    try:
        with open(FILE, "r") as f:
            data = json.load(f)

        print("Contenido encontrado:")
        print(data)

    except Exception as e:
        print("ERROR LEYENDO JSON:", e)
        return

    if not data:
        print("JSON VACIO")
        return

    print("PICKS ENCONTRADOS")

    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

    try:
        res = requests.get(url, timeout=20)
        games = res.json()
        print("Juegos MLB cargados")
    except Exception as e:
        print("ERROR MLB:", e)
        return

    print("✅ PICKS CALIFICADOS")
