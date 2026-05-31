import os
import json
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
WEIGHTS_FILE = "mlb_weights.json"


# -----------------------------
# PESOS AUTO-OPTIMIZABLES
# -----------------------------
DEFAULT_WEIGHTS = {
    "era": 9.0,
    "whip": 6.0,
    "offense": 7.0
}


def load_weights():
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_WEIGHTS.copy()


def save_weights(weights):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f)


weights = load_weights()


# -----------------------------
# PITCHER STATS
# -----------------------------
def get_pitcher_stats(player_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        data = requests.get(url, timeout=10).json()

        stats = data.get("stats", [])
        if not stats or not stats[0].get("splits"):
            return None, None

        stat = stats[0]["splits"][0]["stat"]
        return stat.get("era"), stat.get("whip")

    except:
        return None, None


# -----------------------------
# PITCHERS
# -----------------------------
def get_probable_pitchers(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()

        pitchers = data.get("gameData", {}).get("probablePitchers", {})

        away = pitchers.get("away", {})
        home = pitchers.get("home", {})

        return {
            "away": {"name": away.get("fullName"), "id": away.get("id")},
            "home": {"name": home.get("fullName"), "id": home.get("id")}
        }

    except:
        return None


# -----------------------------
# STATS PITCHER
# -----------------------------
def enrich_pitchers(pitchers):
    away_era, away_whip = (None, None)
    home_era, home_whip = (None, None)

    if pitchers["away"]["id"]:
        away_era, away_whip = get_pitcher_stats(pitchers["away"]["id"])

    if pitchers["home"]["id"]:
        home_era, home_whip = get_pitcher_stats(pitchers["home"]["id"])

    pitchers["away"]["era"] = away_era
    pitchers["away"]["whip"] = away_whip

    pitchers["home"]["era"] = home_era
    pitchers["home"]["whip"] = home_whip

    return pitchers


# -----------------------------
# TEAM DATA
# -----------------------------
def get_team_data():
    try:
        url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
        data = requests.get(url, timeout=10).json()

        teams = {}

        for record in data.get("records", []):
            for t in record.get("teamRecords", []):
                name = t["team"]["name"]

                runs = float(t.get("runsScored", 0))
                games = float(t.get("gamesPlayed", 1))
                rpg = runs / games

                teams[name] = {"rpg": rpg}

        return teams

    except:
        return {}


# -----------------------------
# MODELO BASE
# -----------------------------
def model(away, home, teams):
    a = 50
    h = 50

    if away and home:

        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])
            a += diff * weights["era"]
            h -= diff * weights["era"]

        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])
            a += diff * weights["whip"]
            h -= diff * weights["whip"]

        away_team = teams.get("away")
        home_team = teams.get("home")

        if away_team and home_team:
            diff = away_team["rpg"] - home_team["rpg"]
            a += diff * weights["offense"]
            h -= diff * weights["offense"]

    total = a + h

    return (a / total) * 100, (h / total) * 100


# -----------------------------
# CLASIFICACIÓN (LENGUAJE HUMANO)
# -----------------------------
def classify(diff):
    if diff >= 15:
        return "🟢 Recomendación Alta (Valor fuerte)", 3
    elif diff >= 9:
        return "🟡 Recomendación Media (Valor moderado)", 2
    elif diff >= 6:
        return "⚪ Recomendación Baja (riesgo alto)", 1
    return "⚪ Sin valor suficiente (evitar)", 0


# -----------------------------
# AUTO-OPTIMIZACIÓN SIMPLE
# -----------------------------
def update_weights(diff):
    # ajuste leve tipo learning rate
    lr = 0.05

    if diff >= 12:
        weights["era"] += lr
        weights["whip"] += lr / 2
        weights["offense"] += lr / 2
    else:
        weights["era"] -= lr / 2
        weights["whip"] -= lr / 2

    # clamp
    for k in weights:
        weights[k] = max(3, min(15, weights[k]))

    save_weights(weights)


# -----------------------------
# PICK
# -----------------------------
def pick(a, h):
    return "Visitante" if a > h else "Local"


# -----------------------------
# FORMAT
# -----------------------------
def fmt(p):
    if not p:
        return "TBD"
    return f"{p['name']} | ERA {p.get('era','N/A')} | WHIP {p.get('whip','N/A')}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()
    teams = get_team_data()

    for game in data.get("dates", [])[0].get("games", []):

        pk = game["gamePk"]

        away_name = game["teams"]["away"]["team"]["name"]
        home_name = game["teams"]["home"]["team"]["name"]

        pitchers = get_probable_pitchers(pk)
        pitchers = enrich_pitchers(pitchers)

        away = pitchers["away"]
        home = pitchers["home"]

        teams_map = {
            "away": {"rpg": teams.get(away_name, {}).get("rpg", 0)},
            "home": {"rpg": teams.get(home_name, {}).get("rpg", 0)}
        }

        away_pct, home_pct = model(away, home, teams_map)

        diff = abs(away_pct - home_pct)

        label, stake = classify(diff)

        if stake == 0:
            continue

        update_weights(diff)

        msg = f"""🏦 MLB QUANT AUTO-OPT 🏦

{away_name} vs {home_name}

Pitcher Visitante: {fmt(away)}
Pitcher Local: {fmt(home)}

📊 Probabilidad:
Visitante: {round(away_pct,1)}%
Local: {round(home_pct,1)}%

📈 {label}
📌 Pick: {pick(away_pct, home_pct)}
💰 Stake: {stake}u

──────────────────
"""

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )

        print(f"Sent {away_name} vs {home_name}")


if __name__ == "__main__":
    main()
