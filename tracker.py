from datetime import datetime
from supabase_client import supabase

# ===========================================
# GUARDAR PICK + HISTORIAL
# ===========================================

def save_pick(game, pick_type, pick_value, confidence=None, level=None):

    try:

        today = datetime.now().strftime("%Y-%m-%d")
        snapshot_time = datetime.now().strftime("%H:%M")

        # Buscar pick activo del juego
        existing = (
            supabase
            .table("picks")
            .select("*")
            .eq("game", game)
            .eq("created_at", today)
            .execute()
        )

        # =====================================
        # SI NO EXISTE -> CREAR
        # =====================================
        if not existing.data:

            history = (
                supabase
                .table("pick_history")
                .insert({
                    "game": game,
                    "pick_type": pick_type,
                    "pick_value": str(pick_value),
                    "confidence": confidence,
                    "level": level,
                    "snapshot_time": snapshot_time,
                    "created_at": today
                })
                .execute()
            )

            history_id = history.data[0]["id"]

            supabase.table("picks").insert({
                "game": game,
                "pick_type": pick_type,
                "pick_value": str(pick_value),
                "result": "PENDIENTE",
                "created_at": today,
                "confidence": confidence,
                "level": level,
                "graded": False,
                "history_id": history_id
            }).execute()

            print(f"✅ PICK NUEVO: {game}")
            return

        # =====================================
        # SI EXISTE -> VERIFICAR CAMBIOS
        # =====================================
        current = existing.data[0]

        changed = (
            current.get("pick_type") != pick_type
            or str(current.get("pick_value")) != str(pick_value)
            or current.get("confidence") != confidence
        )

        if not changed:
            print(f"⚠️ SIN CAMBIOS: {game}")
            return

        # Guardar snapshot histórico
        history = (
            supabase
            .table("pick_history")
            .insert({
                "game": game,
                "pick_type": pick_type,
                "pick_value": str(pick_value),
                "confidence": confidence,
                "level": level,
                "snapshot_time": snapshot_time,
                "created_at": today
            })
            .execute()
        )

        history_id = history.data[0]["id"]

        # Actualizar pick principal
        (
            supabase
            .table("picks")
            .update({
                "pick_type": pick_type,
                "pick_value": str(pick_value),
                "confidence": confidence,
                "level": level,
                "history_id": history_id
            })
            .eq("game", game)
            .eq("created_at", today)
            .execute()
        )

        print(f"📈 PICK ACTUALIZADO: {game}")

    except Exception as e:
        print("❌ ERROR GUARDANDO PICK")
        print(e)

# ===========================================
# LOAD RESULTS
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
# DAILY REPORT
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
