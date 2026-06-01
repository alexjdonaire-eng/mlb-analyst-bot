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

def main():

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    r = requests.get(URL, params=params)

    if r.status_code != 200:
        send_message("❌ Error conectando Odds API")
        return

    games = r.json()

    msg = f"🏦 MLB BOT\n\nJuegos encontrados: {len(games)}"

    send_message(msg)

if __name__ == "__main__":
    main()
