import json
import os
import datetime

MEM_FILE = "fund_memory.json"

INITIAL_BANKROLL = 1000.0
MAX_DRAWDOWN = 0.20  # 20% kill switch


# =========================
# LOAD FUND STATE
# =========================
def load_fund():
    try:
        with open(MEM_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "bankroll": INITIAL_BANKROLL,
            "peak": INITIAL_BANKROLL,
            "pnl": 0,
            "wins": 0,
            "losses": 0,
            "history": []
        }


def save_fund(fund):
    with open(MEM_FILE, "w") as f:
        json.dump(fund, f)


# =========================
# UPDATE RESULT
# =========================
def settle_bet(fund, stake, odds, win):

    if win:
        profit = stake * (odds - 1)
        fund["bankroll"] += profit
        fund["wins"] += 1
    else:
        fund["bankroll"] -= stake
        fund["losses"] += 1

    fund["pnl"] = fund["bankroll"] - INITIAL_BANKROLL

    if fund["bankroll"] > fund["peak"]:
        fund["peak"] = fund["bankroll"]

    drawdown = (fund["peak"] - fund["bankroll"]) / fund["peak"]

    return drawdown


# =========================
# STAKE CONTROL (DYNAMIC)
# =========================
def calculate_stake(fund, edge):

    base_risk = 0.02  # 2%

    if edge > 0.15:
        base_risk = 0.04
    elif edge < 0.05:
        base_risk = 0.01

    return fund["bankroll"] * base_risk


# =========================
# KILL SWITCH
# =========================
def risk_check(drawdown):

    if drawdown >= MAX_DRAWDOWN:
        return False
    return True


# =========================
# ROI METRICS
# =========================
def roi(fund):
    return round((fund["pnl"] / INITIAL_BANKROLL) * 100, 2)


# =========================
# LOG RESULT
# =========================
def log_trade(fund, game, pick, stake, odds, result):

    fund["history"].append({
        "time": str(datetime.datetime.now()),
        "game": game,
        "pick": pick,
        "stake": stake,
        "odds": odds,
        "result": result
    })


# =========================
# MAIN INTERFACE
# =========================
def process_pick(game, pick, odds, edge, win=None):

    fund = load_fund()

    stake = calculate_stake(fund, edge)

    drawdown = 0

    if win is not None:
        drawdown = settle_bet(fund, stake, odds, win)
        log_trade(fund, game, pick, stake, odds, win)

    save_fund(fund)

    return {
        "stake": round(stake, 2),
        "bankroll": round(fund["bankroll"], 2),
        "roi": roi(fund),
        "drawdown": round(drawdown * 100, 2),
        "active": risk_check(drawdown)
    }


# =========================
# FUND STATUS REPORT
# =========================
def fund_status():

    fund = load_fund()
    dd = (fund["peak"] - fund["bankroll"]) / fund["peak"]

    return {
        "bankroll": fund["bankroll"],
        "pnl": fund["pnl"],
        "roi": roi(fund),
        "drawdown": round(dd * 100, 2),
        "active": dd < MAX_DRAWDOWN
        }
