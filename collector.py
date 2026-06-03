import os
import requests
import json
from datetime import datetime

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
API_KEY = os.getenv("ODDS_API_KEY")

MEM_FILE = "market_memory.json"


def load_memory():
    try:
        with open(MEM_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(data):
    with open(MEM_FILE, "w") as f:
        json.dump(data, f)


def run():

    print("📡 COLLECTOR V5.2 STEAM ENGINE START")

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

    data = r.json()
    memory = load_memory()

    games = []

    for g in data:

        try:
            book = g["bookmakers"][0]
            outcomes = book["markets"][0]["outcomes"]

            odds = {o["name"]: o["price"] for o in outcomes}

            home = g["home_team"]
            away = g["away_team"]

            key = f"{away}vs{home}"

            previous = memory.get(key)

            movement = 0

            if previous:

                old_odds = previous["odds"]

                for team in odds:
                    if team in old_odds:

                        old = old_odds[team]
                        new = odds[team]

                        # 🔥 cambio relativo real
                        change = (old - new) / old
                        movement += change

            steam_score = movement * 100

            memory[key] = {
                "odds": odds,
                "time": datetime.utcnow().isoformat()
            }

            games.append({
                "home": home,
                "away": away,
                "odds": odds,
                "movement": steam_score
            })

        except Exception:
            continue

    save_memory(memory)

    print(f"📊 Games loaded: {len(games)}")

    return games
