from supabase_client import supabase

# =========================
# CARGAR RESULTADOS
# =========================

def load_results():

    response = supabase.table("picks").select("*").execute()
    rows = response.data or []

    data = {}

    for item in rows:

        created = item.get("created_at", "")

        if created:
            day = created[:10]
        else:
            from datetime import datetime
            day = datetime.now().strftime("%Y-%m-%d")

        if day not in data:
            data[day] = []

        data[day].append({
            "game": item.get("game"),
            "pick_type": item.get("pick_type"),
            "pick_value": item.get("pick_value"),
            "result": item.get("result", "PENDIENTE"),
            "confidence": item.get("confidence", 0),
            "level": item.get("level", "")
        })

    return data


# =========================
# GUARDAR PICK
# =========================

def save_pick(
    game,
    pick_type,
    pick_value,
    confidence=0,
    level=""
):

    try:

        from datetime import datetime

        supabase.table("picks").insert({
            "game": game,
            "pick_type": pick_type,
            "pick_value": pick_value,
            "result": "PENDIENTE",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "confidence": confidence,
            "level": level,
            "graded": False
        }).execute()

        print("✅ PICK GUARDADO EN SUPABASE")

    except Exception as e:

        print("❌ ERROR SUPABASE")
        print(e)


# =========================
# ACTUALIZAR RESULTADO
# =========================

def update_pick(
    game,
    pick_type,
    result
):

    try:

        supabase.table("picks") \
            .update({
                "result": result,
                "graded": True
            }) \
            .eq("game", game) \
            .eq("pick_type", pick_type) \
            .execute()

        print(
            f"✅ RESULTADO ACTUALIZADO: "
            f"{game} | {pick_type} -> {result}"
        )

    except Exception as e:

        print("❌ ERROR UPDATE")
        print(e)


# =========================
# REPORTE GENERAL
# =========================

def daily_report():

    data = load_results()

    wins = 0
    losses = 0

    report = "📊 RESULTADOS\n\n"

    for day in data:

        report += f"📅 {day}\n\n"

        for item in data[day]:

            emoji = "⏳"

            if item["result"] == "GANO":
                emoji = "✅"
                wins += 1

            elif item["result"] == "PERDIO":
                emoji = "❌"
                losses += 1

            report += (
                f"{emoji} {item['game']}\n"
                f"Pick: {item['pick_type']} → {item['pick_value']}\n"
                f"Confianza: {item.get('confidence', 0)}%\n"
                f"Nivel: {item.get('level', '')}\n\n"
            )

    total = wins + losses

    winrate = (
        round(wins / total * 100, 1)
        if total > 0
        else 0
    )

    report += (
        "\n📈 RECORD GENERAL\n\n"
        f"✅ Ganados: {wins}\n"
        f"❌ Perdidos: {losses}\n"
        f"🎯 Win Rate: {winrate}%"
    )

    return report
