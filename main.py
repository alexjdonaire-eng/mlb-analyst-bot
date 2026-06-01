import os
import requests
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# =========================
# TELEGRAM
# =========================
def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )

# =========================

# PROBABILIDAD

# =========================

def prob(odds):
    return 1 / odds

def remove_vig(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total

# =========================

# MODELO BASE MLB

# =========================

def modelo_mlb(team_a, team_b):

    ratings = {
        "Los Angeles Dodgers": 60,
        "New York Yankees": 58,
        "Philadelphia Phillies": 57,
        "Atlanta Braves": 57,
        "Houston Astros": 56,
        "Detroit Tigers": 55,
        "Minnesota Twins": 54,
        "Milwaukee Brewers": 54,
        "Tampa Bay Rays": 53,
        "San Francisco Giants": 52,
        "Seattle Mariners": 52,
        "Arizona Diamondbacks": 52,
        "San Diego Padres": 52,
        "Kansas City Royals": 50,
        "Texas Rangers": 50,
        "Cleveland Guardians": 50,
        "Cincinnati Reds": 48,
        "Los Angeles Angels": 47,
        "St. Louis Cardinals": 47,
        "Washington Nationals": 46,
        "Miami Marlins": 45,
        "Pittsburgh Pirates": 45,
        "Athletics": 44,
        "Toronto Blue Jays": 44,
        "New York Mets": 44,
        "Boston Red Sox": 43,
        "Chicago Cubs": 43,
        "Baltimore Orioles": 43,
        "Colorado Rockies": 40,
        "Chicago White Sox": 38
    }

    a = ratings.get(team_a, 50)
    b = ratings.get(team_b, 50)

    print(team_a, a)
    print(team_b, b)

    total = a + b

    return a / total, b / total
# =========================

# MAIN

# =========================

def main():

print("EJECUTANDO MAIN")

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

reporte = "⚾ ANÁLISIS MLB DEL DÍA ⚾\n\n"

for game in games:

    home = game["home_team"]
    away = game["away_team"]

    if not game["bookmakers"]:
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

    # MERCADO
    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    # MODELO
    m_home, m_away = modelo_mlb(home, away)

    # EDGE
    edge_home = m_home - p_home
    edge_away = m_away - p_away

    edge = max(edge_home, edge_away)

    mejor = home if edge_home > edge_away else away

    # CONFIANZA
    if edge >= 0.20:
        confianza = "🔥 MUY ALTA"
    elif edge >= 0.15:
        confianza = "✅ ALTA"
    elif edge >= 0.10:
        confianza = "⚠️ MEDIA"
    else:
        confianza = "❌ BAJA"

    # FILTRO
    if edge < 0.10:
        continue

    reporte += (
        f"⚾ {away} vs {home}\n"
        f"🎯 Pick: {mejor}\n"
        f"📈 Edge: {round(edge * 100, 2)}%\n"
        f"🎯 Confianza: {confianza}\n\n"
    )

if reporte != "⚾ ANÁLISIS MLB DEL DÍA ⚾\n\n":
    send_message(reporte)
else:
    send_message("❌ No se encontraron picks con valor hoy.")
```

print("BOT INICIADO")

if **name** == "**main**":
main()
