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
# LOAD CLEAN DATA
# =========================

def load_history():
    rows = []

    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    r = json.loads(line)

                    if "game_id" not in r:
                        continue
                    if "odds" not in r:
                        continue
                    if "time" not in r:
                        continue

                    rows.append(r)

                except:
                    continue
    except:
        pass

    return rows


# =========================
# GROUP BY GAME
# =========================

def group(rows):
    games = {}

    for r in rows:
        games.setdefault(r["game_id"], []).append(r)

    for g in games:
        games[g].sort(key=lambda x: x["time"])

    return games


# =========================
# CLV CALCULATION CORE
# =========================

def compute_clv(series):
    if len(series) < 2:
        return 0

    open_odds = series[0]
    close_odds = series[-1]

    if open_odds == 0:
        return 0

    return (open_odds - close_odds) / open_odds


# =========================
# VALUE MODEL (conservador real)
# =========================

def model_prob(series):
    if len(series) < 3:
        return 0

    avg = sum(series[-4:]) / len(series[-4:])
    return 1 / avg


# =========================
# ANALYSIS ENGINE (CLV CORE)
# =========================

def analyze_game(rows):

    if len(rows) < 6:
        return None

    teams = rows[0]["odds"].keys()
    signals = []

    for team in teams:

        series = [r["odds"][team] for r in rows if team in r["odds"]]

        if len(series) < 6:
            continue

        clv = compute_clv(series)

        open_odds = series[0]
        close_odds = series[-1]

        model = model_prob(series)
        implied = 1 / close_odds if close_odds else 0

        if model == 0:
            continue

        edge = model - implied

        # =========================
        # MARKET EFFICIENCY SCORE
        # =========================
        volatility = max(series) - min(series)

        efficiency = abs(clv) * 2 + volatility * 0.5

        # =========================
        # SMART MONEY SIGNAL
        # =========================
        smart_money = (
            clv > 0.015 and      # line moved in your favor
            edge > 0.01 and      # real value
            efficiency > 0.8     # meaningful market movement
        )

        score = (edge * 150) + (clv * 120) + efficiency

        if smart_money:

            signals.append({
                "team": team,
                "open": open_odds,
                "close": close_odds,
                "clv": clv,
                "edge": edge,
                "efficiency": efficiency,
                "score": score
            })

    return signals


# =========================
# MAIN REPORT
# =========================

def main():

    rows = load_history()
    games = group(rows)

    ranked = []

    for gid, rows in games.items():

        signals = analyze_game(rows)

        if not signals:
            continue

        game = rows[-1]

        text = f"🏦 {game['away_team']} vs {game['home_team']}\n\n"

        best = 0

        for s in signals:

            direction = "📉 CLV positive steam" if s["clv"] > 0 else "📈 reverse market"

            text += (
                f"🔥 {s['team']}\n"
                f"{direction}\n"
                f"Open → Close: {s['open']} → {s['close']}\n"
                f"CLV: {round(s['clv']*100,2)}%\n"
                f"Edge: {round(s['edge']*100,2)}%\n"
                f"Market efficiency: {round(s['efficiency'],2)}\n"
                f"Score: {round(s['score'],2)}\n\n"
            )

            best = max(best, s["score"])

        ranked.append((best, text))

    ranked.sort(reverse=True, key=lambda x: x[0])

    if not ranked:
        report = "🏦 CLV TRADING ENGINE\n\n⚠️ No market inefficiencies detected."
    else:
        report = "🏦 CLV TRADING ENGINE\n\n"
        for _, text in ranked[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("CLV ENGINE SENT")


if __name__ == "__main__":
    main()
