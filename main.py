import os
import requests
import json
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"


def get_games():
    r = requests.get(
        URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    print("STATUS:", r.status_code)

    if r.status_code != 200:
        print("ERROR RESPONSE:", r.text)
        return []

    return r.json()


def main():
    print("🚀 MLB DIAGNOSTIC MODE")

    games = get_games()

    print("TOTAL GAMES:", len(games))

    if len(games) > 0:
        print("FIRST GAME:")
        print(json.dumps(games[0], indent=2))

    print("FINISHED")


if __name__ == "__main__":
    main()
