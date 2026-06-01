import os
import requests
import time

# =========================
# CONFIG (SEGURA)
# =========================
TOKEN = os.getenv("8916331113:AAGR-Uh8mjEIx_TjJhPfIb2FVOcGDJI_Sew")
CHAT_ID = os.getenv("5163780989")

BANKROLL = 1000

# =========================
# TELEGRAM
# =========================
def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM NO CONFIGURADO")
        print(text)
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# ODDS (SIMULADO - luego API real)
# =========================
def get_odds():
    return {
        "home_odds": 1.92,
        "away_odds": 2.05
    }


def implied_prob(odds):
    return 1 / odds


# =========================
# MODELO (BASE)
# =========================
def model():
    # placeholder del modelo MLB
    return 0.54, 0.46


# =========================
# STEAM DETECTION
# =========================
steam_memory = {}

def save_open(game_id, odds):
    steam_memory[game_id] = {
        "open": odds,
        "time": time.time()
    }


def detect_steam(game_id, current_odds):
    if game_id not in steam_memory:
        return None

    open_odds = steam_memory[game_id]["open"]

    move = open_odds - current_odds
    pct = (move / open_odds) * 100

    speed = pct / (time.time() - steam_memory[game_id]["time"] + 1)

    if pct > 3 and speed > 0.25:
        return True

    return False


# =========================
# CLV
# =========================
def clv(model_p, market_p):
    return model_p - market_p


# =========================
# KELLY
# =========================
def ev(prob, odds):
    return (prob * (odds - 1)) - (1 - prob)


def kelly(prob, odds):
    e = ev(prob, odds)
    if e <= 0:
        return 0
    return e / (odds - 1)


def position_size(bankroll, prob, odds, clv_val, steam_ok):

    k = kelly(prob, odds) * 0.25

    risk = 1.0
    if clv_val > 0.02:
        risk += 0.4
    else:
        risk -= 0.3

    if steam_ok:
        risk += 0.4
    else:
        risk -= 0.4

    risk = max(0.1, min(risk, 1.5))

    stake = bankroll * k * risk

    max_bet = bankroll * 0.05
    min_bet = bankroll * 0.002

    if stake > max_bet:
        stake = max_bet

    if stake < min_bet:
        return 0

    return round(stake, 2)


# =========================
# BOT PRINCIPAL
# =========================
def run():

    game_id = "MLB_GAME_001"

    odds = get_odds()

    home_odds = odds["home_odds"]
    away_odds = odds["away_odds"]

    home_p = implied_prob(home_odds)
    away_p = implied_prob(away_odds)

    model_home, model_away = model()

    model_p = max(model_home, model_away)
    market_p = max(home_p, away_p)

    pick = "HOME" if model_home > model_away else "AWAY"

    clv_val = clv(model_p, market_p)

    save_open(game_id, home_odds)
    steam_ok = detect_steam(game_id, home_odds)

    bet = clv_val > 0 and steam_ok

    stake = position_size(
        BANKROLL,
        model_p,
        home_odds,
        clv_val,
        steam_ok
    )

    msg = f"""
🏦 MLB FUND BOT v5 🏦

⚾ PICK: {pick}

📊 MODEL: {round(model_p*100,2)}%
📉 MARKET: {round(market_p*100,2)}%

📈 CLV: {round(clv_val*100,3)}%

🚨 STEAM: {"YES" if steam_ok else "NO"}

💰 STAKE: ${stake}

🎯 DECISION: {"BET" if bet else "NO BET"}

──────────────────
"""

    send_message(msg)


if __name__ == "__main__":
    run()
