from datetime import datetime
from supabase_client import supabase

# ===========================================
# GUARDAR PICK
# ===========================================

def save_pick(game, pick_type, pick_value, confidence=None, level=None):

    try:

        today = datetime.now().strftime("%Y-%m-%d")

        # Evitar duplicados del mismo día
        existing = (
            supabase
            .table("picks")
            .select("*")
            .eq("game", game)
            .eq("pick_type", pick_type)
            .eq("pick_value", str(pick_value))
            .eq("created_at", today)
            .execute()
        )

        if existing.data:
            print(f"⚠️ PICK YA EXISTE: {game}")
            return

        supabase.table("picks").insert({
            "game": game,
            "pick_type": pick_type,
            "pick_value": str(pick_value),
            "result": "PENDIENTE",
            "created_at": today,
            "confidence": confidence,
            "level": level,
            "graded": False
        }).execute()

        print("✅ PICK GUARDADO EN SUPABASE")

    except Exception as e:
        print("❌ ERROR GUARDANDO PICK")
        print(e)

# ===========================================
# CARGAR RESULTADOS
# ===========================================

def load_results():

    try:

        response = (
            supabase
            .table("picks")
            .select("*")
            .execute()
        )

        data = response.data or []

        results = {}

        for row in data:

            date = row.get("created_at")

            if not date:
                continue

            if date not in results:
                results[date] = []

            results[date].append({
                "game": row.get("game"),
                "result": row.get("result", "PENDIENTE")
            })

        return results

    except Exception as e:
        print("❌ ERROR LOAD_RESULTS")
        print(e)
        return {}

# ===========================================
# REPORTE DIARIO
# ===========================================

def daily_report():

    try:

        response = (
            supabase
            .table("picks")
            .select("*")
            .execute()
        )

        rows = response.data or []

        wins = len([r for r in rows if r.get("result") == "GANO"])
        losses = len([r for r in rows if r.get("result") == "PERDIO"])
        pending = len([r for r in rows if r.get("result") == "PENDIENTE"])

        total = wins + losses

        winrate = round((wins / total) * 100, 1) if total else 0

        return {
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "winrate": winrate
        }

    except Exception as e:
        print("❌ ERROR DAILY_REPORT")
        print(e)

        return {
            "wins": 0,
            "losses": 0,
            "pending": 0,
            "winrate": 0
        }
