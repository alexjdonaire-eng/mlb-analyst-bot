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
# LOAD HISTORY SAFE
# =========================

def load_history():
    rows = []

    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)

                    # VALIDACIÓN BÁSICA
                    if not data.get("game_id"):
                        continue
                    if not data.get("odds"):
                        continue
                    if not data.get("home_team") or not data.get("away_team"):
                        continue

                    rows.append(data)

                except:
                    continue
    except:
        pass

    return rows


# =========================
# DEDUPLICATION ENGINE
# =========================

def deduplicate(rows):
    seen = set()
    clean = []

    for r in rows:

        key = (
            r["game_id"],
            r["time"],
            str(sorted(r["odds"].items()))
        )

        if key in seen:
            continue

        seen.add(key)
        clean.append(r)

    return clean


# =========================
# GROUP GAMES PROPERLY
# =========================

def group_games(rows):
    games = {}

    for r in rows:
        gid = r["game_id"]
        games.setdefault(gid, []).append(r)

    # ordenar snapshots por tiempo
    for gid in games:
        games[gid].sort(key=lambda x: x["time"])

    return games


# =========================
# VALUE MODEL SAFE
# =========================

def model_prob(series):
    if len(series) < 3:
        return 0

    avg = sum(series[-3:]) / len(series[-3:])
    return 1 / avg


# =========================
# ANALYSIS ENGINE SAFE
# =========================

def analyze_game(rows):

    if len(rows) < 4:
        return None

    teams = rows[0]["odds"].keys()
    signals = []

    for team in teams:

        series = []
        for r in rows:
            if team in r["odds"]:
                series.append(r["odds"][team])

        # VALIDACIÓN CRÍTICA
        if len(series) < 4:
            continue

        start = series[0]
        end = series[-1]

        change = end - start
        volatility = max(series) - min(series)

        momentum = sum(
            1 for i in range(1, len(series))
            if series[i] < series[i - 1]
        ) / (len(series) - 1)

        model = model_prob(series)
        implied = 1 / end if end != 0 else 0

        if model == 0:
            continue

        edge = model - implied

        score = (edge * 100) + (momentum * 10) + (volatility * 0.5)

        # 🔥 FILTRO BALANCEADO (NO OVERFITTING)
        if edge > 0.01 and momentum > 0.45:

            signals.append({
                "team": team,
                "start": start,
                "end": end,
                "change": change,
                "edge": edge,
                "momentum": momentum,
                "score": score
            })

    return signals


# =========================
# MAIN
# =========================

def main():

    history = load_history()

    print("RAW HISTORY:", len(history))

    history = deduplicate(history)

    print("DEDUPED:", len(history))

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

            text += (
                f"🔥 {s['team']}\n"
                f"Edge: {round(s['edge']*100,2)}%\n"
                f"Momentum: {round(s['momentum'],2)}\n"
                f"Score: {round(s['score'],2)}\n\n"
            )

            best = max(best, s["score"])

        ranked.append((best, text))

    ranked.sort(reverse=True, key=lambda x: x[0])

    if not ranked:
        report = "🏦 DATA PIPELINE FIXED\n\n⚠️ No clean opportunities detected yet."
    else:
        report = "🏦 DATA PIPELINE FIXED\n\n"
        for _, text in ranked[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("PIPELINE FIXED SENT")


if __name__ == "__main__":
    main()
