import json
import os
from datetime import datetime

FILE = "/data/daily_results.json"


# =========================
# CARGAR RESULTADOS
# =========================

def load_results():

    if not os.path.exists(FILE):
        return {}

    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}


# =========================
# GUARDAR RESULTADOS
# =========================

def save_results(data):

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# =========================
# GUARDAR PICK
# =========================

def save_pick(game, pick_type, pick_value):

    data = load_results()

    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data:
        data[today] = []

    # Evitar duplicados
    for item in data[today]:

        if (
            item["game"] == game and
            item["pick_type"] == pick_type and
            item["pick_value"] == pick_value
        ):
            return

    data[today].append({
        "game": game,
        "pick_type": pick_type,
        "pick_value": pick_value,
        "result": "PENDIENTE"
    })

    save_results(data)


# =========================
# ACTUALIZAR RESULTADO
# =========================

def update_pick(game, result):

    data = load_results()

    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data:
        return

    for item in data[today]:

        if item["game"] == game:
            item["result"] = result

    save_results(data)


# =========================
# REPORTE DEL DÍA
# =========================

def daily_report():

    data = load_results()

    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data:
        return "⚠️ Sin resultados."

    wins = 0
    losses = 0

    report = "📊 RESULTADOS DEL DÍA\n\n"

    for item in data[today]:

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
        winrate = round(
            wins / total * 100,
            1
        )

    report += (
        f"\n📈 RECORD DEL DÍA\n\n"
        f"✅ Ganados: {wins}\n"
        f"❌ Perdidos: {losses}\n"
        f"🎯 Win Rate: {winrate}%"
    )

    return report
