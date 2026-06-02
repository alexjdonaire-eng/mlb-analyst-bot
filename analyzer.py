import json
import os

HISTORY_FILE = "market_history.jsonl"

START_BANKROLL = 1000


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
# CORE METRICS
# =========================

def clv(series):
    if len(series) < 2:
        return 0
    return (series[0] - series[-1]) / series[0]


def edge(series):
    if len(series) < 4:
        return 0
    avg = sum(series[-5:]) / len(series[-5:])
    return (1 / avg) - (1 / series[-1])


# =========================
# SIMULATED TRADE ENGINE
# =========================

def simulate(edge_val, clv_val):

    # hedge fund logic:
    # CLV + edge = expected profitability signal

    score = (edge_val * 120) + (clv_val * 100)

    if score > 5:
        return 1.15
    elif score > 2:
        return 1.05
    elif score > 0:
        return 1.01
    elif score > -2:
        return 0.98
    else:
        return 0.95


# =========================
# DASHBOARD ENGINE
# =========================

def dashboard():

    rows = load()
    games = group(rows)

    bankroll = START_BANKROLL
    peak = bankroll

    bets = 0
    wins = 0

    equity_curve = [bankroll]

    clv_list = []
    edge_list = []

    worst_streak = 0
    current_streak = 0

    for gid, rows in games.items():

        if len(rows) < 6:
            continue

        teams = rows[0]["odds"].keys()

        for team in teams:

            series = [r["odds"][team] for r in rows if team in r["odds"]]

            if len(series) < 6:
                continue

            clv_val = clv(series)
            edge_val = edge(series)

            if clv_val < 0.005 or edge_val < 0.005:
                continue

            ret = simulate(edge_val, clv_val)

            bankroll *= ret
            equity_curve.append(bankroll)

            bets += 1

            if ret > 1:
                wins += 1
                current_streak = 0
            else:
                current_streak += 1
                worst_streak = max(worst_streak, current_streak)

            clv_list.append(clv_val)
            edge_list.append(edge_val)

            peak = max(peak, bankroll)

    # =========================
    # METRICS
    # =========================

    roi = (bankroll - START_BANKROLL) / START_BANKROLL * 100
    winrate = (wins / bets * 100) if bets else 0
    avg_clv = sum(clv_list) / len(clv_list) if clv_list else 0
    avg_edge = sum(edge_list) / len(edge_list) if edge_list else 0
    drawdown = (peak - bankroll) / peak * 100 if peak else 0

    # =========================
    # REPORT
    # =========================

    print("\n🏦 QUANT DASHBOARD PRO\n")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Bets: {bets}")
    print(f"Winrate: {round(winrate,2)}%")
    print(f"ROI: {round(roi,2)}%")
    print(f"Final bankroll: {round(bankroll,2)}")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Avg CLV: {round(avg_clv,4)}")
    print(f"Avg Edge: {round(avg_edge,4)}")
    print(f"Max Drawdown: {round(drawdown,2)}%")
    print(f"Worst losing streak: {worst_streak}")
    print("━━━━━━━━━━━━━━━━━━━━━━")

    print("\n📈 EQUITY CURVE (last 10 points):")
    print([round(x,2) for x in equity_curve[-10:]])


if __name__ == "__main__":
    dashboard()
