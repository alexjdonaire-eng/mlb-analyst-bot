import os
import requests
import time

# =========================
# CONFIG CORRECTA
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

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


# =========================
# ODDS (SIMULADO)
# =========================
def get_odds():
    return {"home_odds": 1.92, "away_odds": 2.05}


def implied_prob(odds):
    return 1 / odds


# =========================
# MODELO
# =========================
def model():
    return 0.54, 0.46


# =========================
# CLV
# =========================
def clv(model_p, market_p):
    return model_p - market_p


# =========================
# STEAM
# =========================
steam_memory = {}

def save_open(game_id, odds):
    steam_memory[game_id] = {"open": odds, "time": time.time()}


def detect_steam(game_id, current_odds):
    if game_id not in steam_memory:
        return False

    open_odds = steam_memory[game_id]["open"]
    move = open_odds - current_odds
    pct = (move / open_odds) * 100

    return pct > 3


# =========================
# BOT
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

    stake = BANKROLL * 0.01 if bet else 0

    msg = f"""
🏦 MLB BOT FIXED 🏦

⚾ PICK: {pick}

📊 MODEL: {round(model_p*100,2)}%
📉 MARKET: {round(market_p*100,2)}%

📈 CLV: {round(clv_val*100,3)}%

🚨 STEAM: {"YES" if steam_ok else "NO"}

💰 STAKE: ${stake}

🎯 DECISION: {"BET" if bet else "NO BET"}
"""

    send_message(msg)


if __name__ == "__main__":
    run()
