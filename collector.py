import requests
import random

# =========================
# CONFIG (placeholder APIs)
# =========================
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"


# =========================
# SIMULATED PITCHER DB (REEMPLAZABLE CON API REAL)
# =========================
PITCHER_DB = {
    "Philadelphia Phillies": {
        "Zack Wheeler": {"ERA": 2.52, "WHIP": 1.04},
        "Aaron Nola": {"ERA": 3.01, "WHIP": 1.09},
    },
    "Los Angeles Dodgers": {
        "Tyler Glasnow": {"ERA": 3.12, "WHIP": 1.15},
        "Walker Buehler": {"ERA": 3.45, "WHIP": 1.18},
    },
    "default": {
        "TBD": {"ERA": "-", "WHIP": "-"}
    }
}


# =========================
# SIMULATED ODDS MOVEMENT ENGINE
# (REEMPLAZAR CON API REAL DE ODDS HISTORY)
# =========================
def get_market_movement():
    return round(random.uniform(-18, 18), 2)


def get_steam(movement):
    if movement <= -10:
        return "🔥 SHARP MONEY IN"
    elif movement >= 10:
        return "⚪ PUBLIC HEAVY"
    else:
        return "⚪ NEUTRAL"


# =========================
# PICK PITCHERS LOGIC
# =========================
def get_pitchers(home, away):

    home_pitchers = PITCHER_DB.get(home, PITCHER_DB["default"])
    away_pitchers = PITCHER_DB.get(away, PITCHER_DB["default"])

    home_name = list(home_pitchers.keys())[0]
    away_name = list(away_pitchers.keys())[0]

    return {
        "pitcher_home": {
            "name": home_name,
            "ERA": home_pitchers[home_name]["ERA"],
            "WHIP": home_pitchers[home_name]["WHIP"],
        },
        "pitcher_away": {
            "name": away_name,
            "ERA": away_pitchers[away_name]["ERA"],
            "WHIP": away_pitchers[away_name]["WHIP"],
        },
    }


# =========================
# MAIN COLLECTOR
# =========================
def run():

    # 🔥 EN PRODUCCIÓN AQUÍ IRÍA ODDS API REAL
    games_raw = [
        ("San Diego Padres", "Philadelphia Phillies"),
        ("Los Angeles Dodgers", "Arizona Diamondbacks"),
        ("Pittsburgh Pirates", "Houston Astros"),
        ("Kansas City Royals", "Cincinnati Reds"),
        ("San Francisco Giants", "Milwaukee Brewers"),
        ("Chicago White Sox", "Minnesota Twins"),
        ("Colorado Rockies", "Los Angeles Angels"),
        ("Baltimore Orioles", "Boston Red Sox"),
        ("Detroit Tigers", "Tampa Bay Rays"),
        ("Cleveland Guardians", "New York Yankees"),
        ("New York Mets", "Seattle Mariners"),
        ("Toronto Blue Jays", "Atlanta Braves"),
    ]

    games = []

    for away, home in games_raw:

        movement = get_market_movement()

        pitchers = get_pitchers(home, away)

        game = {
            "game": f"{away} vs {home}",
            "away_team": away,
            "home_team": home,

            # odds simulation placeholder (puedes conectar API real)
            "opening_odds": round(random.uniform(-150, -110), 2),
            "current_odds": round(random.uniform(-170, -100), 2),

            "movement": movement,
            "steam": get_steam(movement),

            # pitchers REAL STRUCTURE
            **pitchers
        }

        games.append(game)

    return games
