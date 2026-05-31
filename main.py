import os
import requests

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

        away_id = away.get("id")
        home_id = home.get("id")

        away_era, away_whip = None, None
        home_era, home_whip = None, None

        if away_id:
            away_era, away_whip = get_pitcher_stats(away_id)

        if home_id:
            home_era, home_whip = get_pitcher_stats(home_id)

        return {
            "away": {
                "name": away.get("fullName"),
                "era": away_era,
                "whip": away_whip
            },
            "home": {
                "name": home.get("fullName"),
                "era": home_era,
                "whip": home_whip
            }
        }

    except:
        return None


# -----------------------------
# OFENSIVA
# -----------------------------
def get_team_offense():
    try:
        url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
        data = requests.get(url, timeout=10).json()

        offense = {}

        for record in data.get("records", []):
            for team in record.get("teamRecords", []):
                name = team["team"]["name"]
                runs = float(team.get("runsScored", 0))
                games = float(team.get("gamesPlayed", 1))
                offense[name] = runs / games

        return offense

    except:
        return {}


# -----------------------------
# MODELO PRO (MEJOR BALANCEADO)
# -----------------------------
def get_win_probability(away, home, offense):
    try:
        away_score = 50
        home_score = 50

        if not away or not home:
            return None, None

        # ERA (peso alto)
        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])
            away_score += diff * 8
            home_score -= diff * 8

        # WHIP (peso medio)
        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])
            away_score += diff * 5
            home_score -= diff * 5

        # OFENSIVA
        away_rpg = offense.get(away.get("team"))
        home_rpg = offense.get(home.get("team"))

        if away_rpg and home_rpg:
            diff = away_rpg - home_rpg
            away_score += diff * 6
            home_score -= diff * 6

        total = away_score + home_score

        away_pct = (away_score / total) * 100
        home_pct = (home_score / total) * 100

        return round(away_pct, 1), round(home_pct, 1)

    except:
        return None, None


# -----------------------------
# CONFIANZA PRO
# -----------------------------
def get_confidence(diff):
    if diff >= 15:
        return "🔥 ALTA CONFIANZA"
    elif diff >= 8:
        return "🟡 MEDIA CONFIANZA"
    return "⚖️ BAJA CONFIANZA"


# -----------------------------
# STAKE (UNIDADES)
# -----------------------------
def get_stake(diff):
    if diff >= 15:
        return "💰 Stake: 3u (Fuerte)"
    elif diff >= 10:
        return "💰 Stake: 2u (Media)"
    elif diff >= 8:
        return "💰 Stake: 1u (Baja)"
    return None


# -----------------------------
# PICK
# -----------------------------
def get_pick(away_pct, home_pct, diff):
    if diff < 8:
        return None

    if away_pct > home_pct:
        team = "Visitante"
    else:
        team = "Local"

    return f"📌 PICK: {team}"


# -----------------------------
# FORMATO
# -----------------------------
def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD"

    return f"{p['name']} | ERA: {p['era'] or 'N/A'} | WHIP: {p['whip'] or 'N/A'}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()
    offense = get_team_offense()

    dates = data.get("dates", [])

    if not dates:
        msg = "⚾ No hay juegos hoy."
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
        )
        return

    for game in dates[0].get("games", []):

        game_pk = game.get("gamePk")

        away_team = game["teams"]["away"]["team"]["name"]
        home_team = game["teams"]["home"]["team"]["name"]

        pitchers = get_probable_pitchers(game_pk)

        away = pitchers["away"] if pitchers else None
        home = pitchers["home"] if pitchers else None

        if away:
            away["team"] = away_team
        if home:
            home["team"] = home_team

        away_pct, home_pct = get_win_probability(away, home, offense)

        if away_pct is None or home_pct is None:
            continue

        diff = abs(away_pct - home_pct)

        # 🔥 FILTRO PRO (solo value bets)
        pick = get_pick(away_pct, home_pct, diff)

        if not pick:
            continue

        confidence = get_confidence(diff)
        stake = get_stake(diff)

        msg = f"""⚾ MLB PRO ANALYST ⚾

{away_team} vs {home_team}

Pitcher Visitante: {format_pitcher(away)}
Pitcher Local: {format_pitcher(home)}

📊 Probabilidad:
Visitante: {away_pct}%
Local: {home_pct}%

{confidence}
{pick}
{stake if stake else ""}

──────────────────
"""

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )

        print(f"Sent: {away_team} vs {home_team}")


if __name__ == "__main__":
    main()
