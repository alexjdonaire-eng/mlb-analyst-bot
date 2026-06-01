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
```

def main():

```
params = {
    "apiKey": ODDS_API_KEY,
    "regions": "us",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

games = requests.get(
    URL,
    params=params,
    timeout=30
).json()

print("JUEGOS:", len(games))

for game in games:

    try:

        home = game["home_team"]
        away = game["away_team"]

        if not game.get("bookmakers"):
            continue

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

        p_home, p_away = remove_vig(
            p_home,
            p_away
        )

        favorito = home if p_home > p_away else away

        msg = f"""
```

🏦 MLB MARKET BOT

⚾ {away} vs {home}

📊 Mercado

{away}: {round(p_away*100,1)}%
{home}: {round(p_home*100,1)}%

📌 Favorito:
{favorito}

──────────────────
"""

```
        send_message(msg)

        print("ENVIADO:", away, "vs", home)

    except Exception as e:

        print("ERROR:", e)
```

if **name** == "**main**":
main()
