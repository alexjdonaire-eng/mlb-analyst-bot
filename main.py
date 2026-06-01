# =========================
# config.py
# =========================

import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"


# =========================
# utils/math_utils.py
# =========================

def prob(odds):
    return 1 / odds if odds else 0


def remove_vig(p1, p2):
    total = p1 + p2
    if total == 0:
        return 0, 0
    return p1 / total, p2 / total


# =========================
# models/mlb_model.py
# =========================

import math

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


def predict(team_a, team_b):
    a = ratings.get(team_a, 50)
    b = ratings.get(team_b, 50)

    diff = a - b

    prob_a = 1 / (1 + math.exp(-diff / 10))
    prob_b = 1 - prob_a

    return prob_a, prob_b


# =========================
# services/telegram.py
# =========================

import requests

def send_message(text, TOKEN, CHAT_ID):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# services/odds_api.py
# =========================

import requests

def get_games(URL, ODDS_API_KEY):

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        r = requests.get(URL, params=params, timeout=10)

        if r.status_code != 200:
            return []

        return r.json()

    except Exception as e:
        print("Odds API error:", e)
        return []


# =========================
# core/analyzer.py
# =========================

from models.mlb_model import predict
from utils.math_utils import prob, remove_vig

def analyze_game(home, away, home_odds, away_odds):

    p_home = prob(home_odds)
    p_away = prob(away_odds)

    p_home, p_away = remove_vig(p_home, p_away)

    m_home, m_away = predict(home, away)

    edge_home = m_home - p_home
    edge_away = m_away - p_away

    if edge_home > edge_away:
        return home, edge_home
    else:
        return away, edge_away


# =========================
# main.py
# =========================

from config import TOKEN, CHAT_ID, URL, ODDS_API_KEY
from services.telegram import send_message
from services.odds_api import get_games
from core.analyzer import analyze_game


def main():

    games = get_games(URL, ODDS_API_KEY)

    if not games:
        send_message("❌ Error o sin datos de partidos", TOKEN, CHAT_ID)
        return

    reporte = "⚾ MLB PICKS DEL DÍA ⚾\n\n"

    for game in games:

        home = game["home_team"]
        away = game["away_team"]

        if not game.get("bookmakers"):
            continue

        book = game["bookmakers"][0]

        if not book.get("markets"):
            continue

        outcomes = book["markets"][0].get("outcomes", [])

        if not outcomes:
            continue

        home_odds = None
        away_odds = None

        for o in outcomes:
            if o["name"] == home:
                home_odds = o["price"]
            if o["name"] == away:
                away_odds = o["price"]

        if not home_odds or not away_odds:
            continue

        pick, edge = analyze_game(home, away, home_odds, away_odds)

        if edge < 0.10:
            continue

        reporte += (
            f"{away} vs {home}\n"
            f"🎯 Pick: {pick}\n"
            f"📈 Edge: {round(edge * 100, 2)}%\n\n"
        )

    send_message(reporte, TOKEN, CHAT_ID)


if __name__ == "__main__":
    main()
