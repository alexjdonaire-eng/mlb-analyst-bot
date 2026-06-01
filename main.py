import os
import requests
import json
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# archivo local (Railway lo mantiene mientras esté activo)
STATE_FILE = "odds_state.json"


def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def implied_prob(odds):
    return 1 / odds


def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total


def main():

    state = load_state()

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    r = requests.get(URL, params=params)

    if r.status_code != 200:
        send_message("❌ Error Odds API")
        return

    games = r.json()

    report = []

    for game in games:

        home = game["home_team"]
        away = game["away_team"]
        game_id = game.get("id", f"{home}_vs_{away}")

        book = game["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            continue

        # mercado actual
        p_home = implied_prob(home_odds)
        p_away = implied_prob(away_odds)

        p_home, p_away = remove_vig(p_home, p_away)

        # guardar open odds si no existe
        if game_id not in state:
            state[game_id] = {
                "open_home": home_odds,
                "open_away": away_odds
            }

        open_home = state[game_id]["open_home"]

        # CLV simple (home side)
        clv_home = implied_prob(open_home) - p_home

        report.append(
            f"""⚾ {away} vs {home}
CLV Home: {round(clv_home*100,3)}%
"""
        )

    save_state(state)

    msg = "🏦 CLV TRACKER MLB\n\n" + "\n".join(report[:10])

    send_message(msg)


if __name__ == "__main__":
    main()
