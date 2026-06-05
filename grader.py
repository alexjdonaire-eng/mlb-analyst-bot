from supabase_client import supabase

def grade_picks():

    print("=== GRADER START ===")

    try:

        response = (
            supabase
            .table("picks")
            .select("*")
            .eq("result", "PENDIENTE")
            .execute()
        )

        picks = response.data or []

        print(f"Picks pendientes: {len(picks)}")

        # Aquí luego agregaremos la lógica MLB real

        print("✅ GRADER EJECUTADO")

    except Exception as e:

        print("❌ ERROR GRADER")
        print(e)
