import os
import requests
from datetime import datetime, timezone

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
API_KEY = os.getenv("ODDS_API_KEY")

def run():
    print("📡 COLLECTOR START")

    try:
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
        r.raise_for_status()
        data = r.json()

        games = []

        for g in data:
            try:
                book = g["bookmakers"][0]
                outcomes = book["markets"][0]["outcomes"]

                odds = {o["name"]: o["price"] for o in outcomes}

                games.append({
                    "home": g["home_team"],
                    "away": g["away_team"],
                    "odds": odds
                })

            except:
                continue

        print(f"📊 Games loaded: {len(games)}")
        return games

    except Exception as e:
        print(f"❌ Collector error: {e}")
        return []
