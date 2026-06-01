import os
import requests
import optuna
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

# -----------------------------
# MODELO (PESOS BASE)
# -----------------------------
def model(away, home, offense, away_team, home_team, w):

    a = 50
    h = 50

    a += (home["era"] - away["era"]) * w["era"]
    h -= (home["era"] - away["era"]) * w["era"]

    a += (home["whip"] - away["whip"]) * w["whip"]
    h -= (home["whip"] - away["whip"]) * w["whip"]

    if away_team in offense and home_team in offense:
        diff = offense[away_team] - offense[home_team]
        a += diff * w["offense"]
        h -= diff * w["offense"]

    total = a + h

    return a / total, h / total


# -----------------------------
# PITCHERS
# -----------------------------
def get_pitcher_stats(pid):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=season&group=pitching"
        data = requests.get(url).json()

        s = data["stats"][0]["splits"][0]["stat"]
        return float(s.get("era", 0)), float(s.get("whip", 0))
    except:
        return 0, 0


def get_pitchers(game_pk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    data = requests.get(url).json()

    p = data.get("gameData", {}).get("probablePitchers", {})

    return {
        "away": p.get("away", {}),
        "home": p.get("home", {})
    }


# -----------------------------
# OFENSIVA
# -----------------------------
def get_offense():
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
    data = requests.get(url).json()

    teams = {}

    for r in data["records"]:
        for t in r["teamRecords"]:
            name = t["team"]["name"]
            runs = float(t.get("runsScored", 0))
            games = float(t.get("gamesPlayed", 1))
            teams[name] = runs / games

    return teams


# -----------------------------
# CLV REAL (OPEN vs CLOSE SIMULADO/REAL)
# -----------------------------
def clv(open_prob, close_prob):
    return open_prob - close_prob


# -----------------------------
# SIMULACIÓN DE MERCADO (REEMPLAZABLE POR BOOK REAL)
# -----------------------------
def market_prob(team_strength):
    # proxy simple de mercado
    return team_strength * 0.98


# -----------------------------
# DATASET PARA OPTUNA
# -----------------------------
def build_dataset():

    data = requests.get(SCHEDULE_URL).json()
    offense = get_offense()

    dataset = []

    games = data.get("dates", [])[0].get("games", [])

    for g in games:

        pk = g["gamePk"]

        away_team = g["teams"]["away"]["team"]["name"]
        home_team = g["teams"]["home"]["team"]["name"]

        pitchers = get_pitchers(pk)

        away = pitchers["away"]
        home = pitchers["home"]

        away_stats = {"era": 0, "whip": 0}
        home_stats = {"era": 0, "whip": 0}

        if away.get("id"):
            away_stats["era"], away_stats["whip"] = get_pitcher_stats(away["id"])

        if home.get("id"):
            home_stats["era"], home_stats["whip"] = get_pitcher_stats(home["id"])

        # placeholder weights (se optimizan con optuna)
        w = {"era": 8, "whip": 6, "offense": 7}

        a, h = model(away_stats, home_stats, offense, away_team, home_team, w)

        model_prob = max(a, h)
        market = market_prob(model_prob)

        dataset.append({
            "model": model_prob,
            "market": market
        })

    return dataset


# -----------------------------
# OPTUNA OBJECTIVE (CLV MAXIMIZATION)
# -----------------------------
def objective(trial):

    w = {
        "era": trial.suggest_float("era", 1, 20),
        "whip": trial.suggest_float("whip", 1, 20),
        "offense": trial.suggest_float("offense", 1, 20)
    }

    data = build_dataset()

    total_clv = 0

    for d in data:
        total_clv += clv(d["model"], d["market"])

    return total_clv


# -----------------------------
# OPTIMIZACIÓN BAYESIANA
# -----------------------------
def optimize_model():

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)

    print("\n🏦 BEST MODEL:")
    print(study.best_params)

    return study.best_params


# -----------------------------
# LIVE BOT (SIMPLIFICADO)
# -----------------------------
def run_live(weights):

    data = requests.get(SCHEDULE_URL).json()
    offense = get_offense()

    games = data.get("dates", [])[0].get("games", [])

    for g in games:

        pk = g["gamePk"]

        away_team = g["teams"]["away"]["team"]["name"]
        home_team = g["teams"]["home"]["team"]["name"]

        pitchers = get_pitchers(pk)

        away = pitchers["away"]
        home = pitchers["home"]

        away_stats = {"era": 0, "whip": 0}
        home_stats = {"era": 0, "whip": 0}

        if away.get("id"):
            away_stats["era"], away_stats["whip"] = get_pitcher_stats(away["id"])

        if home.get("id"):
            home_stats["era"], home_stats["whip"] = get_pitcher_stats(home["id"])

        a, h = model(away_stats, home_stats, offense, away_team, home_team, weights)

        pick = "VISITANTE" if a > h else "LOCAL"

        msg = f"""🏦 MLB QUANT FUND v3 🏦

{away_team} vs {home_team}

📊 Probabilidad:
Visitante: {round(a*100,2)}%
Local: {round(h*100,2)}%

📌 PICK: {pick}

──────────────────
"""

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )

        print("Sent:", away_team, home_team)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    print("🔁 Running Optuna optimization...")
    best = optimize_model()

    print("🚀 Running live bot...")

    run_live(best)
