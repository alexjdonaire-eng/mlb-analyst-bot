import json
import os
from datetime import datetime

FILE = "daily_results.json"

def load_results():

    if not os.path.exists(FILE):
        return {}

    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_results(data):

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_pick(game, pick):

    data = load_results()

    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data:
        data[today] = []

    data[today].append({
        "game": game,
        "pick": pick,
        "result": "PENDIENTE"
    })

    save_results(data)

def update_pick(game, result):

    data = load_results()

    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data:
        return

    for item in data[today]:

        if item["game"] == game:
            item["result"] = result

    save_results(data)

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
            f"Pick: {item['pick']}\n\n"
        )

    total = wins + losses

    winrate = 0

    if total > 0:
        winrate = round(
            wins / total * 100,
            1
        )

    report += (
        f"\n📈 RECORD\n\n"
        f"✅ Ganados: {wins}\n"
        f"❌ Perdidos: {losses}\n"
        f"🎯 Win Rate: {winrate}%"
    )

    return report
