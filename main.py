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
# MODELO BASE MLB (TU EDGE)
# =========================
def modelo_mlb(team_a, team_b):
    """
    Modelo simple:
    - fuerza ofensiva simulada
    - fuerza defensiva simulada
    """

    ofensiva = {
        "default": 4.5  # carreras promedio
    }

    defensa = {
        "default": 4.5  # ERA promedio
    }

    # scoring base
    a = 50
    b = 50

    # ventaja aleatoria estructurada por nombre (proxy simple)
    hash_a = sum(ord(c) for c in team_a) % 10
    hash_b = sum(ord(c) for c in team_b) % 10

    a += hash_a * 1.2
    b += hash_b * 1.2

    total = a + b

    return a / total, b / total


# =========================
# MAIN
# =========================
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

        # =========================
        # MERCADO
        # =========================
        p_home = prob(home_odds)
        p_away = prob(away_odds)

        p_home, p_away = remove_vig(p_home, p_away)

        # =========================
        # MODELO PROPIO
        # =========================
        m_home, m_away = modelo_mlb(home, away)

        # =========================
        # EDGE REAL
        # =========================
 # seguridad de rangos
m_home = min(max(m_home, 0), 1)
m_away = min(max(m_away, 0), 1)

p_home = min(max(p_home, 0), 1)
p_away = min(max(p_away, 0), 1)

# edge real
edge_home = m_home - p_home
edge_away = m_away - p_away

edge = max(edge_home, edge_away)

# límite anti-explosión
edge = max(min(edge), -1)
edge = min(edge, 1)

# favorito
mejor = home if edge_home > edge_away else away

        # =========================
        # FILTRO REAL
        # =========================
        if edge < 0.01:
            print("Sin valor:", away, "vs", home)
            continue

        msg = (
    f"🏦 SISTEMA\n\n"
    f"⚾ {away} vs {home}\n\n"
    f"📊 Mercado:\n"
    f"{away}: {round(p_away*100,2)}%\n"
    f"{home}: {round(p_home*100,2)}%\n\n"
    f"🧠 Modelo:\n"
    f"{away}: {round(m_away*100,2)}%\n"
    f"{home}: {round(m_home*100,2)}%\n\n"
    f"📈 Edge: {round(edge*100,3)}%\n\n"
    f"📌 Favorito modelo: {mejor}\n"
        )

        send_message(msg)


if __name__ == "__main__":
    main()
