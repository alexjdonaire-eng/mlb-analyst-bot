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

        # Juegos MLB
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

        r = requests.get(url, timeout=20)
        data = r.json()

        for date in data.get("dates", []):

            for game in date.get("games", []):

                status = (
                    game.get("status", {})
                    .get("detailedState", "")
                )

                if status != "Final":
                    continue

                home_team = game["teams"]["home"]["team"]["name"]
                away_team = game["teams"]["away"]["team"]["name"]

                home_score = game["teams"]["home"]["score"]
                away_score = game["teams"]["away"]["score"]

                print(
                    f"FINAL: {away_team} {away_score} - "
                    f"{home_score} {home_team}"
                )

        print("✅ GRADER EJECUTADO")

    except Exception as e:

        print("❌ ERROR GRADER")
        print(e)
