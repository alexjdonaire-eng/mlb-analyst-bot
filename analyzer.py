import os
import json
import requests
import math

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
    except:
        pass


# =========================
# LOAD DATA
# =========================

def load():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if "game_id" in r and "odds" in r:
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
    g = {}
    for r in rows:
        g.setdefault(r["game_id"], []).append(r)

    for k in g:
        g[k].sort(key=lambda x: x["time"])

    return g


# =========================
# CLV CORE
# =========================

def clv(series):
    if len(series) < 2:
        return 0
    return (series[0] - series[-1]) / series[0]


# =========================
# IMPROVED PROB MODEL
# =========================

def model(series):
    if len(series) < 4:
        return 0
    return 1 / (sum(series[-5:]) / len(series[-5:]))


# =========================
# KELLY FRACTION (RISK ENGINE)
# =========================

def kelly(edge, odds):
    if odds <= 1:
        return 0
    b = odds - 1
    p = max(min(edge + (1 / odds), 0.99), 0.01)
    q = 1 - p
    return max((b * p - q) / b, 0)


# =========================
# SIGNAL ENGINE
# =========================

def analyze(rows):

    if len(rows) < 6:
        return None

    teams = rows[0]["odds"].keys()
    signals = []

    for team in teams:

        series = [r["odds"][team] for r in rows if team in r["odds"]]

        if len(series) < 6:
            continue

        open_odds = series[0]
        close_odds = series[-1]

        clv_val = clv(series)
        model_p = model(series)

        implied = 1 / close_odds if close_odds else 0

        if model_p == 0:
            continue

        edge = model_p - implied

        volatility = max(series) - min(series)

        liquidity = abs(clv_val) + volatility * 0.3

        # =========================
        # EDGE QUALITY SCORE
        # =========================
        score = (edge * 120) + (clv_val * 100) + liquidity

        # =========================
        # STAKING (PORTFOLIO ENGINE)
        # =========================
        kelly_size = kelly(edge, close_odds)
        stake = round(kelly_size * 100, 2)

        # =========================
        # FILTER INSTITUCIONAL
        # =========================
        if clv_val > 0.01 and edge > 0.015 and liquidity > 0.8:

            signals.append({
                "team": team,
                "open": open_odds,
                "close": close_odds,
                "clv": clv_val,
                "edge": edge,
                "liquidity": liquidity,
                "score": score,
                "stake": stake
            })

    return signals


# =========================
# MAIN DESK REPORT
# =========================

def main():

    rows = load()
    games = group(rows)

    ranked = []

    for gid, rows in games.items():

        signals = analyze(rows)

        if not signals:
            continue

        game = rows[-1]

        text = f"🏦 {game['away_team']} vs {game['home_team']}\n\n"

        best = 0

        for s in signals:

            direction = "📉 smart steam" if s["clv"] > 0 else "📈 reverse move"

            text += (
                f"🔥 {s['team']}\n"
                f"{direction}\n"
                f"Open → Close: {s['open']} → {s['close']}\n"
                f"CLV: {round(s['clv']*100,2)}%\n"
                f"Edge: {round(s['edge']*100,2)}%\n"
                f"Liquidity: {round(s['liquidity'],2)}\n"
                f"Stake (Kelly %): {s['stake']}%\n"
                f"Score: {round(s['score'],2)}\n\n"
            )

            best = max(best, s["score"])

        ranked.append((best, text))

    ranked.sort(reverse=True, key=lambda x: x[0])

    if not ranked:
        report = "🏦 QUANT DESK\n\n⚠️ No institutional edges detected."
    else:
        report = "🏦 QUANT DESK - LIVE SIGNALS\n\n"
        for _, text in ranked[:5]:
            report += text + "────────────────────\n\n"

    send(report)
    print("QUANT DESK SENT")


if __name__ == "__main__":
    main()
