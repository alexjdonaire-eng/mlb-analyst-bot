import json
import os

HISTORY_FILE = "market_history.jsonl"


# =========================
# LOAD DATA
# =========================

def load():
    rows = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            try:
                r = json.loads(line)
                if "game_id" in r and "odds" in r:
                    rows.append(r)
            except:
                continue
    return rows


# =========================
# GROUP
# =========================

def group(rows):
    g = {}
    for r in rows:
        g.setdefault(r["game_id"], []).append(r)

    for k in g:
        g[k].sort(key=lambda x: x["time"])

    return g


# =========================
# CLV
# =========================

def clv(series):
    if len(series) < 2:
        return 0
    return (series[0] - series[-1]) / series[0]


# =========================
# EDGE MODEL (same logic as live system)
# =========================

def edge(series):
    if len(series) < 4:
        return 0

    avg = sum(series[-5:]) / len(series[-5:])
    model = 1 / avg
    implied = 1 / series[-1]

    return model - implied


# =========================
# SIMULATED RETURN ENGINE
# =========================

def simulate_trade(edge, clv_value):

    # hedge fund assumption:
    # CLV + edge predicts long term EV

    expected_return = (edge * 100) + (clv_value * 80)

    # normalize risk
    if expected_return > 5:
        return 1.2  # big win
    elif expected_return > 2:
        return 1.05
    elif expected_return > 0:
        return 1.01
    elif expected_return > -2:
        return 0.98
    else:
        return 0.95


# =========================
# BACKTEST ENGINE
# =========================

def backtest():

    rows = load()
    games = group(rows)

    bankroll = 1000
    peak = bankroll
    max_dd = 0

    bets = 0
    wins = 0

    total_clv = 0
    total_edge = 0

    for gid, rows in games.items():

        if len(rows) < 6:
            continue

        teams = rows[0]["odds"].keys()

        for team in teams:

            series = [r["odds"][team] for r in rows if team in r["odds"]]

            if len(series) < 6:
                continue

            clv_value = clv(series)
            e = edge(series)

            # filter hedge fund style
            if clv_value < 0.005 or e < 0.005:
                continue

            ret = simulate_trade(e, clv_value)

            bankroll *= ret

            bets += 1

            if ret > 1:
                wins += 1

            total_clv += clv_value
            total_edge += e

            # drawdown tracking
            if bankroll > peak:
                peak = bankroll

            dd = (peak - bankroll) / peak
            max_dd = max(max_dd, dd)

    # =========================
    # REPORT
    # =========================

    if bets == 0:
        print("NO VALID TRADES FOUND")
        return

    print("\n🏦 BACKTEST HEDGE FUND REPORT\n")

    print("Bets:", bets)
    print("Win rate (simulated):", round(wins / bets * 100, 2), "%")
    print("Final bankroll:", round(bankroll, 2))
    print("ROI:", round((bankroll - 1000) / 1000 * 100, 2), "%")

    print("Avg CLV:", round(total_clv / bets, 4))
    print("Avg Edge:", round(total_edge / bets, 4))

    print("Max Drawdown:", round(max_dd * 100, 2), "%")


if __name__ == "__main__":
    backtest()
