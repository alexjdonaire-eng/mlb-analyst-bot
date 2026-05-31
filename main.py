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
# TEAM OFFENSE + FORM
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

                # ofensiva base
                rpg = runs / games

                # forma (proxy: record últimos juegos simplificado)
                w = float(t.get("wins", 0))
                l = float(t.get("losses", 0))
                form = (w - l) / max((w + l), 1)

                teams[name] = {
                    "rpg": rpg,
                    "form": form
                }

        return teams

    except:
        return {}


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
# MODELO CUANTITATIVO
# -----------------------------
def get_probability(away, home, teams):
    try:
        away_score = 50
        home_score = 50

        if not away or not home:
            return None, None

        # ---------------- ERA ----------------
        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])
            away_score += diff * 9
            home_score -= diff * 9

        # ---------------- WHIP ----------------
        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])
            away_score += diff * 6
            home_score -= diff * 6

        # ---------------- OFFENSE + FORM ----------------
        away_team = teams.get(away.get("team"))
        home_team = teams.get(home.get("team"))

        if away_team and home_team:

            # ofensiva
            diff_rpg = away_team["rpg"] - home_team["rpg"]
            away_score += diff_rpg * 7
            home_score -= diff_rpg * 7

            # forma reciente (proxy bullpen + momentum)
            diff_form = away_team["form"] - home_team["form"]
            away_score += diff_form * 5
            home_score -= diff_form * 5

        total = away_score + home_score

        return (
            round((away_score / total) * 100, 1),
            round((home_score / total) * 100, 1)
        )

    except:
        return None, None


# -----------------------------
# CONFIDENCIA PRO
# -----------------------------
def get_confidence(diff):
    if diff >= 15:
        return "🔥 ALTA (PRO)"
    elif diff >= 9:
        return "🟡 MEDIA"
    return "⚖️ BAJA"


# -----------------------------
# STAKE AVANZADO
# -----------------------------
def get_stake(diff):
    if diff >= 15:
        return "💰 3u (Fuerte Value)"
    elif diff >= 12:
        return "💰 2u (Value medio)"
    elif diff >= 9:
        return "💰 1u (ligero value)"
    return None


# -----------------------------
# PICK
# -----------------------------
def get_pick(away_pct, home_pct, diff):
    if diff < 9:
        return None

    return "📌 PICK: Visitante" if away_pct > home_pct else "📌 PICK: Local"


# -----------------------------
# FORMAT
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
    teams = get_team_data()

    dates = data.get("dates", [])

    if not dates:
        msg = "⚾ No hay juegos hoy."
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
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

        away_pct, home_pct = get_probability(away, home, teams)

        if away_pct is None or home_pct is None:
            continue

        diff = abs(away_pct - home_pct)

        pick = get_pick(away_pct, home_pct, diff)

        if not pick:
            continue

        conf = get_confidence(diff)
        stake = get_stake(diff)

        msg = f"""⚾ MLB QUANT MODEL ⚾

{away_team} vs {home_team}

Pitcher Visitante: {format_pitcher(away)}
Pitcher Local: {format_pitcher(home)}

📊 Probabilidad:
Visitante: {away_pct}%
Local: {home_pct}%

{conf}
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
