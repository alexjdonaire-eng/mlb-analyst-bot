import os
import time
import json
import requests
from datetime import datetime, timezone

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

API_KEY = os.getenv("ODDS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LEDGER_FILE = "trades.jsonl"


# =========================
# TELEGRAM
# =========================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
    except:
        pass


# =========================
# DATA FETCH
# =========================

def fetch_odds():
    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        },
        timeout=20
    )

    if r.status_code != 200:
        return []

    return r.json()


# =========================
# FEATURE ENGINE
# =========================

def extract_edge(game):

    if not game.get("bookmakers"):
        return None

    book = game["bookmakers"][0]
    outcomes = book["markets"][0]["outcomes"]

    odds = {o["name"]: o["price"] for o in outcomes}

    if len(odds) < 2:
        return None

    favorite = min(odds, key=odds.get)
    price = odds[favorite]

    implied = 1 / price

    # pseudo model probability (baseline inefficiency model)
    model_prob = implied + 0.03  # small edge assumption

    edge = model_prob - implied

    return favorite, price, edge, odds


# =========================
# STAKING (KELLY CONSERVATIVE)
# =========================

def kelly(edge, odds, bankroll):

    if odds <= 1:
        return 0

    b = odds - 1
    p = min(max(edge + (1 / odds), 0.05), 0.90)
    q = 1 - p

    k = (b * p - q) / b

    return max(k * 0.25, 0) * bankroll  # quarter Kelly


# =========================
# EXECUTION (PAPER TRADING)
# =========================

def execute_trade(game, bankroll):

    res = extract_edge(game)

    if not res:
        return bankroll, None

    team, odds, edge, all_odds = res

    if edge < 0.02:
        return bankroll, None

    stake = kelly(edge, odds, bankroll)

    if stake < 5:
        return bankroll, None

    # simulate outcome (NO REAL RESULTS YET)
    outcome = 1.12 if edge > 0.03 else 0.95

    pnl = stake * (outcome - 1)

    bankroll += pnl

    trade = {
        "time": datetime.now(timezone.utc).isoformat(),
        "team": team,
        "odds": odds,
        "edge": edge,
        "stake": stake,
        "pnl": pnl,
        "bankroll": bankroll
    }

    with open(LEDGER_FILE, "a") as f:
        f.write(json.dumps(trade) + "\n")

    return bankroll, trade


# =========================
# MAIN LOOP (LIVE ENGINE)
# =========================

def run():

    bankroll = 1000

    send("🚀 LIVE TRADING DESK STARTED")

    while True:

        games = fetch_odds()

        trades = 0

        for g in games:

            bankroll, trade = execute_trade(g, bankroll)

            if trade:
                trades += 1

                send(
                    f"⚾ TRADE EXECUTED\n\n"
                    f"{trade['team']}\n"
                    f"Odds: {trade['odds']}\n"
                    f"Edge: {round(trade['edge']*100,2)}%\n"
                    f"Stake: ${round(trade['stake'],2)}\n"
                    f"PnL: ${round(trade['pnl'],2)}\n"
                    f"Bankroll: ${round(bankroll,2)}"
                )

        print(f"Cycle done | trades: {trades} | bankroll: {bankroll}")

        time.sleep(300)  # every 5 minutes


if __name__ == "__main__":
    run()
