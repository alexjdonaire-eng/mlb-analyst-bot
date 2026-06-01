import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")

url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

params = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

r = requests.get(url, params=params)

print("STATUS:", r.status_code)
print(r.text[:500])
