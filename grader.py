from supabase_client import supabase
import requests

def grade_picks():

    print("=== GRADER START ===")

    try:

        response = (
            supabase
            .table("picks")
            .select("*")
            .eq("graded", False)
            .execute()
        )

        picks = response.data or []

        print(f"Picks pendientes: {len(picks)}")

        # FECHA DE PRUEBA
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-06-04"

        r = requests.get(url, timeout=20)

        print("STATUS CODE:", r.status_code)

        data = r.json()

        print("RESPUESTA MLB:")
        print(data)

        for date in data.get("dates", []):

            for game in date.get("games", []):

                status = (
                    game.get("status", {})
                    .get("detailedState", "")
                )

                print("STATUS:", status)

                home_team = game["teams"]["home"]["team"]["name"]
                away_team = game["teams"]["away"]["team"]["name"]

                home_score = game["teams"]["home"].get("score", 0)
                away_score = game["teams"]["away"].get("score", 0)

                print(
                    f"{away_team} {away_score} - "
                    f"{home_score} {home_team}"
                )

        print("✅ GRADER EJECUTADO")

    except Exception as e:

        print("❌ ERROR GRADER")
        print(e)
