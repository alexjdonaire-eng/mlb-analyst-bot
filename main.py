import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

def implied_prob(odds):
return 1 / odds

def remove_vig(p1, p2):
total = p1 + p2
return p1 / total, p2 / total

def send_message(text):
r = requests.post(
f"https://api.telegram.org/bot{TOKEN}/sendMessage",
json={
"chat_id": CHAT_ID,
"text": text
},
timeout=20
)

```
print("STATUS:", r.status_code)
print(r.text)
```

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

print("ODDS STATUS:", response.status_code)

games = response.json()

if not isinstance(games, list):
    print("ERROR API:", games)
    return

print("JUEGOS ENCONTRADOS:", len(games))

for game in games:

    try:

        home = game["home_team"]
        away = game["away_team"]

        bookmakers = game.get("bookmakers", [])

        if not bookmakers:
            continue

        book = bookmakers[0]

        markets = book.get("markets", [])

        if not markets:
            continue

        outcomes = markets[0].get("outcomes", [])

        home_odds = None
        away_odds = None

        for outcome in outcomes:

            if outcome["name"] == home:
                home_odds = outcome["price"]

            if outcome["name"] == away:
                away_odds = outcome["price"]

        if home_odds is None or away_odds is None:
            continue

        p_home = implied_prob(home_odds)
        p_away = implied_prob(away_odds)

        p_home, p_away = remove_vig(
            p_home,
            p_away
        )

        favorito = home if p_home > p_away else away

        mensaje = f"""
```

🏦 MLB MARKET BOT

⚾ {away} vs {home}

📊 Probabilidades de mercado

{away}: {round(p_away * 100, 1)}%
{home}: {round(p_home * 100, 1)}%

📌 Favorito:
{favorito}

──────────────────
"""

```
        send_message(mensaje)

        print("ENVIADO:", away, "vs", home)

    except Exception as e:

        print("ERROR JUEGO:", e)

print("FINALIZADO")
```

if **name** == "**main**":
main()
