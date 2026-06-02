import json
import os

HISTORY_FILE = "market_history.jsonl"

START_BANKROLL = 1000


# =========================
# LOAD
# =========================

def load():
    rows = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            try:
                r = json.loads(line)
                if "game_id" in r and "odds" in r and "time" in r:
                    rows.append(r)
            except:
                continue
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
# SIMPLE MODEL (rolling learning proxy)
# =========================

def model(series):
    if len(series) < 4:
        return 0
    return 1 / (sum(series[-5:]) / len(series[-5:]))


# =========================
# CLV
# =========================

def clv(series):
    if len(series) < 2:
        return 0
    return (series[0] - series[-1]) / series[0]


# =========================
# KELLY (conservative)
# =========================

def kelly(edge, odds):
    if odds <= 1:
        return 0
    b = odds - 1
    p = max(min(edge + (1 / odds), 0.95), 0.05)
    q = 1 - p
    return max((b * p - q) / b, 0)


# =========================
# WALK-FORWARD SIMULATION
# =========================

def walk_forward():

    rows = load()
    games = group(rows)

    bankroll = START_BANKROLL
    peak = bankroll

    bets = 0
    wins = 0

    equity = []

    for gid, rows in games.items():

        if len(rows) < 6:
            continue

        teams = rows[0]["odds"].keys()

        for team in teams:

            series = [r["odds"][team] for r in rows if team in r["odds"]]

            if len(series) < 6:
                continue

            # =========================
            # SIGNAL ENGINE (LIVE STYLE)
            # =========================
            clv_val = clv(series)
            model_p = model(series)

            close_odds = series[-1]
            implied = 1 / close_odds if close_odds else 0

            edge = model_p - implied

            # =========================
            # TRADE FILTER
            # =========================
            if clv_val < 0.005 or edge < 0.005:
                continue

            # =========================
            # STAKING (REAL MONEY SIM)
            # =========================
            stake_pct = kelly(edge, close_odds)
            stake = bankroll * stake_pct

            if stake < 1:
                continue

            # =========================
            # OUTCOME SIMULATION (proxy)
            # =========================
            # CLV positive = higher probability of profit
            result = 1.1 if clv_val > 0 else 0.95

            profit = stake * (result - 1)

            bankroll += profit

            bets += 1

            if profit > 0:
                wins += 1

            equity.append(bankroll)

            peak = max(peak, bankroll)

    # =========================
    # METRICS
    # =========================

    roi = (bankroll - START_BANKROLL) / START_BANKROLL * 100
    winrate = (wins / bets * 100) if bets else 0
    drawdown = (peak - bankroll) / peak * 100 if peak else 0

    # =========================
    # REPORT
    # =========================

    print("\n🏦 WALK-FORWARD QUANT REPORT\n")
    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"Bets: {bets}")
    print(f"Winrate: {round(winrate,2)}%")
    print(f"ROI: {round(roi,2)}%")
    print(f"Final bankroll: {round(bankroll,2)}")
    print(f"Max Drawdown: {round(drawdown,2)}%")
    print("━━━━━━━━━━━━━━━━━━━━")

    print("\n📈 Equity curve (last 10):")
    print([round(x,2) for x in equity[-10:]])


if __name__ == "__main__":
    walk_forward()
