import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

# -----------------------------
# PITCHERS
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

def get_probable_pitchers(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = requests.get(url, timeout=10).json()
        p = data.get("gameData", {}).get("probablePitchers", {})
        away = p.get("away", {})
        home = p.get("home", {})
        return {
            "away": {"name": away.get("fullName"), "id": away.get("id")},
            "home": {"name": home.get("fullName"), "id": home.get("id")}
        }
    except:
        return None

def enrich(p):
    if not p:
        return None
    if p["away"]["id"]:
        p["away"]["era"], p["away"]["whip"] = get_pitcher_stats(p["away"]["id"])
    else:
        p["away"]["era"], p["away"]["whip"] = None, None
    if p["home"]["id"]:
        p["home"]["era"], p["home"]["whip"] = get_pitcher_stats(p["home"]["id"])
    else:
        p["home"]["era"], p["home"]["whip"] = None, None
    return p

# -----------------------------
# OFFENSIVE STATS
# -----------------------------
def get_offense():
    try:
        url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
        data = requests.get(url, timeout=10).json()
        teams = {}
        for r in data.get("records", []):
            for t in r.get("teamRecords", []):
                name = t["team"]["name"]
                runs = float(t.get("runsScored", 0))
                games = float(t.get("gamesPlayed", 1))
                teams[name] = runs / games
        return teams
    except:
        return {}

# -----------------------------
# SCRAPING CUOTAS (ej. DraftKings)
# -----------------------------
def get_odds_dk():
    odds = {}
    try:
        url = "https://www.draftkings.com/odds/mlb"  # ejemplo
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # Extrae los nombres y odds; esto depende del HTML real de la página
        # Placeholder para demostrar
        # odds["Red Sox vs Yankees"] = {"away": 1.9, "home": 1.8}
        # Tienes que ajustar los selectores según el HTML actual de DraftKings
        return odds
    except:
        return odds

# -----------------------------
# MODELO
# -----------------------------
def model(away, home, offense, away_team, home_team):
    a = 50
    h = 50
    if away and home:
        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])
            a += diff * 9
            h -= diff * 9
        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])
            a += diff * 6
            h -= diff * 6
    if away_team in offense and home_team in offense:
        diff = offense[away_team] - offense[home_team]
        a += diff * 7
        h -= diff * 7
    total = a + h
    return round((a / total) * 100, 1), round((h / total) * 100, 1)

# -----------------------------
# CALC CLV
# -----------------------------
def calc_clv(model_pct, odds):
    implied = 1 / odds if odds else None
    if not implied:
        return None
    ev = (model_pct/100 - implied) * odds * 100
    return implied*100, ev

def stake(ev):
    if ev >= 12:
        return "💰💰💰 Alta convicción"
    elif ev >= 6:
        return "💰💰 Valor medio"
    elif ev >= 3:
        return "💰 Valor bajo"
    return None

def pick(a, h):
    return "Visitante" if a > h else "Local"

# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()
    offense = get_offense()
    odds_data = get_odds_dk()

    for game in data.get("dates", [])[0].get("games", []):
        pk = game["gamePk"]
        away_team = game["teams"]["away"]["team"]["name"]
        home_team = game["teams"]["home"]["team"]["name"]
        pitchers = enrich(get_probable_pitchers(pk))
        if not pitchers:
            continue
        away = pitchers["away"]
        home = pitchers["home"]
        away_pct, home_pct = model(away, home, offense, away_team, home_team)
        # Buscar odds
        game_key = f"{away_team} vs {home_team}"
        odds = odds_data.get(game_key, {"away": 2.0, "home": 2.0})
        implied, ev = calc_clv(max(away_pct, home_pct), max(odds.values()))
        if ev < 3:
            continue
        msg = f"""⚾ MLB EDGE MODEL ⚾

{away_team} vs {home_team}

Pitcher Visitante: {away.get('name')} ERA:{away.get('era')} WHIP:{away.get('whip')}
Pitcher Local: {home.get('name')} ERA:{home.get('era')} WHIP:{home.get('whip')}

Modelo:
Visitante: {away_pct}% | Local: {home_pct}%

Odds casa: Visitante {odds['away']} | Local {odds['home']}
EV (valor esperado): {round(ev,2)}%
Pick: {pick(away_pct, home_pct)}
{stake(ev)}

──────────────────
"""
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print(f"Mensaje enviado para {away_team} vs {home_team}")

if __name__ == "__main__":
    main()
