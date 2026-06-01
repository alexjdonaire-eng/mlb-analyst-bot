import os
import requests
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


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


def enrich_pitchers(p):
    if not p:
        return None

    a_id = p["away"]["id"]
    h_id = p["home"]["id"]

    if a_id:
        p["away"]["era"], p["away"]["whip"] = get_pitcher_stats(a_id)
    else:
        p["away"]["era"], p["away"]["whip"] = None, None

    if h_id:
        p["home"]["era"], p["home"]["whip"] = get_pitcher_stats(h_id)
    else:
        p["home"]["era"], p["home"]["whip"] = None, None

    return p


# -----------------------------
# TEAM OFFENSE
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
# MODELO INSTITUCIONAL
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
# EDGE REAL
# -----------------------------
def edge(diff):
    if diff >= 15:
        return "🟢 Fuerte ventaja"
    elif diff >= 9:
        return "🟡 Ventaja moderada"
    return "⚪ Sin ventaja clara"


# -----------------------------
# STAKE SIMPLE (HUMANO)
# -----------------------------
def stake(diff):
    if diff >= 15:
        return "💰💰💰 Alta confianza (riesgo bajo)"
    elif diff >= 10:
        return "💰💰 Confianza media"
    elif diff >= 8:
        return "💰 Confianza baja"
    return None


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
    offense = get_offense()

    games = data.get("dates", [])
    if not games:
        return

    for g in games[0].get("games", []):

        pk = g["gamePk"]

        away_team = g["teams"]["away"]["team"]["name"]
        home_team = g["teams"]["home"]["team"]["name"]

        pitchers = enrich_pitchers(get_probable_pitchers(pk))

        if not pitchers:
            continue

        away = pitchers["away"]
        home = pitchers["home"]

        away_pct, home_pct = model(away, home, offense, away_team, home_team)

        diff = abs(away_pct - home_pct)

        if diff < 8:
            continue  # filtro institucional (ruido eliminado)

        msg = f"""🏦 MLB INSTITUTIONAL MODEL 🏦

{away_team} vs {home_team}

Pitcher Visitante: {fmt(away)}
Pitcher Local: {fmt(home)}

📊 Probabilidad:
Visitante: {away_pct}%
Local: {home_pct}%

📈 {edge(diff)}
📌 Pick: {pick(away_pct, home_pct)}
{stake(diff)}

──────────────────
"""

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )

        print(f"Sent {away_team} vs {home_team}")


if __name__ == "__main__":
    main()
