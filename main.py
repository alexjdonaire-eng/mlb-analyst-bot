import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

def send_message(text):
try:
requests.post(
f"https://api.telegram.org/bot{TOKEN}/sendMessage",
json={
"chat_id": CHAT_ID,
"text": text
},
timeout=20
)
except Exception as e:
print("Error Telegram:", e)

def main():

```
params = {
    "apiKey": ODDS_API_KEY,
    "regions": "us",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

response = requests.get(
    URL,
    params=params,
    timeout=30
)

print("STATUS:", response.status_code)

if response.status_code != 200:
    send_message(
        f"❌ Error Odds API: {response.status_code}"
    )
    return

games = response.json()

send_message(
    f"✅ Odds API conectada\n\n⚾ Juegos MLB encontrados: {len(games)}"
)
```

if **name** == "**main**":
main()
