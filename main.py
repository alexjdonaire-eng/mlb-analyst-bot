import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )

def implied_prob(odds):
    return 1 / odds

def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total

def main():

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

    for game in games:

        home = game["home_team"]
        away = game["away_team"]

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

        p_home = implied_prob(home_odds)
        p_away = implied_prob(away_odds)

        p_home, p_away = remove_vig(p_home, p_away)

        favorite = home if p_home > p_away else away

        msg = f"""🏦 MLB MARKET

⚾ {away} vs {home}

📊 Probabilidades:
{away}: {round(p_away*100,2)}%
{home}: {round(p_home*100,2)}%

📌 Favorito:
{favorite}
"""

        send_message(msg)

if __name__ == "__main__":
    main()
