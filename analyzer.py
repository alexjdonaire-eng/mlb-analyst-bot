import os
import json
import requests

HISTORY_FILE = "market_history.jsonl"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=20
    )


# =========================
# LOAD DATA
# =========================

def load_history():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    except:
        pass
    return rows


def group_games(history):
    games = {}
    for r in history:
        games.setdefault(r["game_id"], []).append(r)
    return games


# =========================
# ANALYSIS ENGINE PRO
# =========================

def analyze_game(rows):

    rows.sort(key=lambda x: x["time"])

    if len(rows) < 4:
        return None

    teams = list(rows[0]["odds"].keys())

    signals = []

    for team in teams:

        series = []

        for r in rows:
            if team in r["odds"]:
                series.append(r["odds"][team])

        if len(series) < 4:
            continue

        start = series[0]
        end = series[-1]

        change = end - start

        # volatilidad total
        volatility = max(series) - min(series)

        # consistencia: cuántas veces bajó consecutivamente
        drops = 0
        for i in range(1, len(series)):
            if series[i] < series[i - 1]:
                drops += 1

        consistency = drops / (len(series) - 1)

        # score pro (clave del sistema)
        score = (abs(change) * 2) + volatility + (consistency * 0.5)

        # filtro sharp real
        if change < -0.12 and volatility > 0.18 and consistency > 0.55:
            signals.append({
                "team": team,
                "start": start,
                "end": end,
                "change": change,
                "volatility": volatility,
                "consistency": round(consistency, 2),
                "score": round(score, 2)
            })

    return signals


# =========================
# MAIN
# =========================

def main():

    history = load_history()
    games = group_games(history)

    report = "🔥 SHARP MONEY PRO SYSTEM MLB\n\n"

    results = []

    for gid, rows in games.items():

        signals = analyze_game(rows)

        if not signals:
            continue

        game = rows[-1]

        text = f"⚾ {game['away_team']} vs {game['home_team']}\n\n"

        for s in signals:

            direction = "📉 dinero entrando fuerte" if s["change"] < 0 else "📈 presión en contra"

            text += (
                f"🔥 {s['team']}\n"
                f"{s['start']} → {s['end']}\n"
                f"{direction}\n"
                f"Score: {s['score']}\n"
                f"Consistencia: {s['consistency']}\n\n"
            )

        results.append((signals[0]["score"], text))

    # ranking global (CLAVE PRO)
    results.sort(reverse=True, key=lambda x: x[0])

    if not results:
        report = "🔥 SHARP MONEY PRO SYSTEM MLB\n\n⚠️ Sin señales institucionales fuertes."
    else:
        report = "🔥 SHARP MONEY PRO SYSTEM MLB\n\n"

        for _, text in results[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("PRO ANALYZER SENT")


if __name__ == "__main__":
    main()
