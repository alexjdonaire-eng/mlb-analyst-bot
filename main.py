import os
import requests
import json
from datetime import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

STORE_FILE = "picks_store.json"


# =========================
# STORAGE
# =========================

def load_picks():
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_picks(picks):
    with open(STORE_FILE, "w") as f:
        json.dump(picks, f)


# =========================
# TELEGRAM
# =========================

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


# =========================
# ODDS
# =========================

def get_odds():
    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )
    return r.json()


# =========================
# MODEL SIMPLE (placeholder tuyo)
# =========================

def fake_model_pick(game):

    home = game["home_team"]
    away = game["away_team"]

    # simplificado (aquí luego conectas tu v6 real)
    return {
        "game": f"{away} vs {home}",
        "pick": home,
        "odds": 2.0,
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================
# CLV CALCULATION
# =========================

def calc_clv(entry, current_odds):

    if not current_odds:
        return None

    open_odds = entry["odds"]
    close_odds = current_odds

    clv = (open_odds - close_odds) / close_odds

    return clv


# =========================
# MAIN LOGIC
# =========================

def main():

    print("🚀 CLV ENGINE V7 RUNNING")

    games = get_odds()

    picks = load_picks()

    # =========================
    # 1. GENERATE NEW PICKS
    # =========================

    for g in games:

        pick = fake_model_pick(g)

        picks.append(pick)

        send(f"🏦 PICK STORED\n{pick['game']}\n🎯 {pick['pick']}\n💰 Odds: {pick['odds']}")

    save_picks(picks)

    # =========================
    # 2. CLV CHECK (SIMPLIFIED)
    # =========================

    report = "📊 CLV REPORT\n\n"

    for p in picks[-10:]:

        # simular cierre (en v8 será real histórico)
        closing_odds = 1.85

        clv = calc_clv(p, closing_odds)

        if clv is None:
            continue

        status = "🟢 EDGE REAL" if clv > 0 else "🔴 NO EDGE"

        report += (
            f"⚾ {p['game']}\n"
            f"🎯 {p['pick']}\n"
            f"📊 CLV: {round(clv*100,2)}%\n"
            f"{status}\n\n"
        )

    send(report)


if __name__ == "__main__":
    main()
