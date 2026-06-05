from supabase_client import supabase

# =========================
# COMPATIBILIDAD CON MAIN.PY
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
            "result": item.get("result", "PENDIENTE")
        })

    return data


# =========================
# GUARDAR PICK
# =========================

def save_pick(game, pick_type, pick_value, confidence=0, level=""):

    try:

        supabase.table("picks").insert({
            "game": game,
            "pick_type": pick_type,
            "pick_value": pick_value,
            "result": "PENDIENTE",
            "confidence": confidence,
            "level": level
        }).execute()

        print("✅ PICK GUARDADO EN SUPABASE")

    except Exception as e:

        print("❌ ERROR SUPABASE")
        print(e)

# =========================
# ACTUALIZAR RESULTADO
# =========================

def update_pick(game, result):

    try:

        supabase.table("picks") \
            .update({"result": result}) \
            .eq("game", game) \
            .execute()

        print("✅ RESULTADO ACTUALIZADO")

    except Exception as e:

        print("❌ ERROR UPDATE")
        print(e)


# =========================
# REPORTE DEL DIA
# =========================

def daily_report():

    data = load_results()

    wins = 0
    losses = 0

    report = "📊 RESULTADOS\n\n"

    for day in data:

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
                f"Pick: {item['pick_type']} → {item['pick_value']}\n\n"
            )

    total = wins + losses

    winrate = round(wins / total * 100, 1) if total else 0

    report += (
        f"\n📈 RECORD\n\n"
        f"✅ Ganados: {wins}\n"
        f"❌ Perdidos: {losses}\n"
        f"🎯 Win Rate: {winrate}%"
    )

    return report
