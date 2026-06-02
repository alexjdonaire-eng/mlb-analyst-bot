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


# =========================
# GROUP BY GAME
# =========================

def group_games(history):
    games = {}
    for r in history:
        gid = r.get("game_id")
        if gid:
            games.setdefault(gid, []).append(r)
    return games


# =========================
# MODEL PROBABILITY (simple baseline)
# =========================

def model_probability(series):
    avg_odds = sum(series[-3:]) / min(3, len(series))
    return 1 / avg_odds


# =========================
# ANALYSIS ENGINE
# =========================

def analyze_game(rows):

    rows.sort(key=lambda x: x["time"])

    if len(rows) < 4:
        return None

    teams = rows[0]["odds"].keys()
    results = []

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
        volatility = max(series) - min(series)

        drops = sum(
            1 for i in range(1, len(series))
            if series[i] < series[i - 1]
        )

        consistency = drops / (len(series) - 1)

        # =========================
        # VALUE BETTING
        # =========================
        implied = 1 / end
        model = model_probability(series)
        value = model - implied

        # =========================
        # SHARP SCORE
        # =========================
        sharp_score = (abs(change) * 2) + volatility + (consistency * 0.5)

        # =========================
        # FINAL SCORE
        # =========================
        final_score = (
            (value * 100) * 0.5 +
            sharp_score * 0.7 +
            (consistency * 10)
        )

        # FILTRO (ajustado para que SÍ salga info)
        if value > 0.01:

            results.append({
                "team": team,
                "start": start,
                "end": end,
                "change": change,
                "value": value,
                "implied": implied,
                "model": model,
                "consistency": consistency,
                "sharp": sharp_score,
                "score": final_score
            })

    return results


# =========================
# MAIN
# =========================

def main():

    history = load_history()
    games = group_games(history)

    print("GAMES:", len(games))

    report = "🏆 SISTEMA FINAL - MLB BETTING ENGINE\n\n"
    ranked = []

    for gid, rows in games.items():

        signals = analyze_game(rows)

        if not signals:
            continue

        game = rows[-1]

        text = f"⚾ {game['away_team']} vs {game['home_team']}\n\n"

        best_score = 0

        for s in signals:

            edge = round(s["value"] * 100, 2)

            direction = "📉 sharp money entrando" if s["change"] < 0 else "📈 presión contraria"

            text += (
                f"🔥 {s['team']}\n"
                f"Odds: {s['start']} → {s['end']}\n"
                f"{direction}\n"
                f"Value Edge: +{edge}%\n"
                f"Sharp Score: {round(s['sharp'],2)}\n"
                f"Consistency: {round(s['consistency'],2)}\n"
                f"FINAL SCORE: {round(s['score'],2)}\n\n"
            )

            best_score = max(best_score, s["score"])

        ranked.append((best_score, text))

    ranked.sort(reverse=True, key=lambda x: x[0])

    print("RANKED:", len(ranked))

    if not ranked:
        report = "🏆 SISTEMA FINAL - MLB BETTING ENGINE\n\n⚠️ Sin oportunidades de valor detectadas."
    else:
        for _, text in ranked[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("SYSTEM FINAL SENT")


if __name__ == "__main__":
    main()
