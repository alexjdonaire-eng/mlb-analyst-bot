from supabase_client import supabase
from datetime import datetime

# =========================
# GUARDAR PICK
# =========================

def save_pick(game, pick_type, pick_value):

    supabase.table("picks").insert({
        "game": game,
        "pick_type": pick_type,
        "pick_value": pick_value,
        "result": "PENDIENTE"
    }).execute()

    print("✅ PICK GUARDADO EN SUPABASE")


# =========================
# ACTUALIZAR RESULTADO
# =========================

def update_pick(game, result):

    supabase.table("picks") \
        .update({"result": result}) \
        .eq("game", game) \
        .execute()

    print("🔄 RESULTADO ACTUALIZADO EN SUPABASE")


# =========================
# REPORTE DEL DÍA
# =========================

def daily_report():

    response = supabase.table("picks").select("*").execute()
    data = response.data

    if not data:
        return "⚠️ Sin resultados."

    wins = 0
    losses = 0

    report = "📊 RESULTADOS DEL DÍA\n\n"

    for item in data:

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

    winrate = 0

    if total > 0:
        winrate = round(wins / total * 100, 1)

    report += (
        f"\n📈 RECORD GENERAL\n\n"
        f"✅ Ganados: {wins}\n"
        f"❌ Perdidos: {losses}\n"
        f"🎯 Win Rate: {winrate}%"
    )

    return report
