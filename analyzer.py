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
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
    except Exception as e:
        print("TELEGRAM ERROR:", e)


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
        gid = r.get("game_id")
        if gid:
            games.setdefault(gid, []).append(r)
    return games


# =========================
# MODEL (baseline + stability)
# =========================

def model_probability(series):
    if len(series) < 3:
        return 0
    avg_odds = sum(series[-3:]) / min(3, len(series))
    return 1 / avg_odds


# =========================
# SHARP DETECTION CORE
# =========================

def analyze_game(rows):

    rows.sort(key=lambda x: x["time"])

    if len(rows) < 5:
        return None

    teams = rows[0]["odds"].keys()
    signals = []

    for team in teams:

        series = [r["odds"][team] for r in rows if team in r["odds"]]

        if len(series) < 5:
            continue

        start = series[0]
        end = series[-1]

        # =========================
        # MOVIMIENTO
        # =========================
        change = end - start
        volatility = max(series) - min(series)

        # steam detection (movimiento sostenido)
        momentum = sum(
            1 for i in range(1, len(series))
            if series[i] < series[i - 1]
        ) / (len(series) - 1)

        # =========================
        # VALUE REAL
        # =========================
        implied_prob = 1 / end
        model_prob = model_probability(series)

        if model_prob == 0:
            continue

        edge = model_prob - implied_prob

        # =========================
        # SHARP SCORE (mejorado)
        # =========================
        sharp_score = (
            abs(change) * 1.5 +
            volatility * 0.8 +
            momentum * 2.0
        )

        # =========================
        # FINAL SCORE PRO
        # =========================
        final_score = (
            edge * 120 +
            sharp_score * 0.6 +
            momentum * 10
        )

        # =========================
        # FILTRO PRO SHARP
        # =========================
        if (
            edge > 0.015 and          # value real mínimo
            sharp_score > 0.8 and     # movimiento real
            momentum > 0.55           # steam confirmado
        ):

            signals.append({
                "team": team,
                "start": start,
                "end": end,
                "change": change,
                "edge": edge,
                "momentum": momentum,
                "sharp_score": sharp_score,
                "final_score": final_score
            })

    return signals


# =========================
# MAIN ENGINE
# =========================

def main():

    history = load_history()
    games = group_games(history)

    print("GAMES:", len(games))

    ranked = []

    for gid, rows in games.items():

        signals = analyze_game(rows)

        if not signals:
            continue

        game = rows[-1]

        text = f"⚾ {game['away_team']} vs {game['home_team']}\n\n"

        best = 0

        for s in signals:

            direction = "📉 steam move" if s["change"] < 0 else "📈 reverse pressure"

            text += (
                f"🔥 {s['team']}\n"
                f"{direction}\n"
                f"Edge: {round(s['edge']*100,2)}%\n"
                f"Momentum: {round(s['momentum'],2)}\n"
                f"Sharp Score: {round(s['sharp_score'],2)}\n"
                f"FINAL SCORE: {round(s['final_score'],2)}\n\n"
            )

            best = max(best, s["final_score"])

        ranked.append((best, text))

    ranked.sort(reverse=True, key=lambda x: x[0])

    if not ranked:
        report = "🏆 PRO SHARP ENGINE\n\n⚠️ Sin señales de sharp money detectadas."
    else:
        report = "🏆 PRO SHARP ENGINE\n\n"
        for _, text in ranked[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("PRO SHARP SENT")


if __name__ == "__main__":
    main()
