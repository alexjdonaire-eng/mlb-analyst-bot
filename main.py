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
# PITCHERS DEL JUEGO
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

        away_era, away_whip = (None, None)
        home_era, home_whip = (None, None)

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
# OFENSIVA SIMPLE (RUNS)
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
# PROBABILIDAD
# -----------------------------
def get_win_probability(away, home, offense):
    try:
        if not away or not home:
            return None, None

        away_score = 50
        home_score = 50

        # ERA
        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])

            if diff > 0.50:
                away_score += 10
                home_score -= 10
            elif diff < -0.50:
                home_score += 10
                away_score -= 10

        # WHIP
        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])

            if diff > 0.15:
                away_score += 5
                home_score -= 5
            elif diff < -0.15:
                home_score += 5
                away_score -= 5

        # OFENSIVA
        if offense:
            away_rpg = offense.get(away.get("team"))
            home_rpg = offense.get(home.get("team"))

            if away_rpg and home_rpg:
                if away_rpg > home_rpg:
                    away_score += 8
                    home_score -= 8
                elif home_rpg > away_rpg:
                    home_score += 8
                    away_score -= 8

        total = away_score + home_score

        return (
            round((away_score / total) * 100, 1),
            round((home_score / total) * 100, 1)
        )

    except:
        return None, None


# -----------------------------
# CONFIANZA
# -----------------------------
def get_confidence(away_pct, home_pct):
    diff = abs(away_pct - home_pct)

    if diff >= 12:
        return "🔥 Alta confianza"
    elif diff >= 6:
        return "🟡 Media confianza"
    else:
        return "⚖️ Baja confianza"


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

    msg = "⚾ MLB ANALYST BOT ⚾\n\n"

    dates = data.get("dates", [])

    if not dates:
        msg += "No hay juegos hoy."
    else:
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

            # 🔥 FILTRO: solo mostrar juegos interesantes
            if away_pct is None or home_pct is None:
                continue

            if abs(away_pct - home_pct) < 5:
                continue

            confidence = get_confidence(away_pct, home_pct)

            msg += f"⚾ {away_team} vs {home_team}\n"
            msg += f"Pitcher Visitante: {format_pitcher(away)}\n"
            msg += f"Pitcher Local: {format_pitcher(home)}\n"

            msg += f"📊 Probabilidad:\n"
            msg += f"Visitante: {away_pct}%\n"
            msg += f"Local: {home_pct}%\n"
            msg += f"🎯 {confidence}\n"

            msg += "\n──────────────────\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

    print("OK")


if __name__ == "__main__":
    main()
        away_era, away_whip = (None, None)
        home_era, home_whip = (None, None)

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
# PROBABILIDAD MEJORADA
# -----------------------------
def get_win_probability(away, home, offense):
    try:
        if not away or not home:
            return None, None

        away_score = 50
        home_score = 50

        # ERA
        if away["era"] and home["era"]:
            diff = float(home["era"]) - float(away["era"])

            if diff > 0.50:
                away_score += 10
                home_score -= 10
            elif diff < -0.50:
                home_score += 10
                away_score -= 10

        # WHIP
        if away["whip"] and home["whip"]:
            diff = float(home["whip"]) - float(away["whip"])

            if diff > 0.15:
                away_score += 5
                home_score -= 5
            elif diff < -0.15:
                home_score += 5
                away_score -= 5

        # OFENSIVA
        if offense:
            away_rpg = offense.get(away.get("team"), None)
            home_rpg = offense.get(home.get("team"), None)

            if away_rpg and home_rpg:
                if away_rpg > home_rpg:
                    away_score += 8
                    home_score -= 8
                elif home_rpg > away_rpg:
                    home_score += 8
                    away_score -= 8

        total = away_score + home_score

        return (
            round((away_score / total) * 100, 1),
            round((home_score / total) * 100, 1)
        )

    except:
        return None, None


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

    msg = "⚾ MLB ANALYST BOT ⚾\n\n"

    dates = data.get("dates", [])

    if not dates:
        msg += "No hay juegos hoy."
    else:
        for game in dates[0].get("games", []):
            game_pk = game.get("gamePk")

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            pitchers = get_probable_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            # agregar nombre equipo dentro de objeto para ofensiva
            if away:
                away["team"] = away_team
            if home:
                home["team"] = home_team

            away_pct, home_pct = get_win_probability(away, home, offense)

            msg += f"⚾ {away_team} vs {home_team}\n"
            msg += f"Pitcher Visitante: {format_pitcher(away)}\n"
            msg += f"Pitcher Local: {format_pitcher(home)}\n"

            if away_pct and home_pct:
                msg += "📊 Probabilidad de victoria:\n"
                msg += f"Visitante: {away_pct}%\n"
                msg += f"Local: {home_pct}%\n"
            else:
                msg += "📊 Probabilidad: Sin datos suficientes\n"

            msg += "\n──────────────────\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

    print("OK")


if __name__ == "__main__":
    main()
# -----------------------------
# MODELO DE PROBABILIDAD
# -----------------------------
def get_win_probability(away, home):
    try:
        if not away or not home:
            return None, None

        away_score = 50
        home_score = 50

        # ERA (peso fuerte)
        if away["era"] and home["era"]:
            era_diff = float(home["era"]) - float(away["era"])

            if era_diff > 0.50:
                away_score += 12
                home_score -= 12
            elif era_diff < -0.50:
                home_score += 12
                away_score -= 12

        # WHIP (peso medio)
        if away["whip"] and home["whip"]:
            whip_diff = float(home["whip"]) - float(away["whip"])

            if whip_diff > 0.15:
                away_score += 6
                home_score -= 6
            elif whip_diff < -0.15:
                home_score += 6
                away_score -= 6

        total = away_score + home_score

        away_pct = round((away_score / total) * 100, 1)
        home_pct = round((home_score / total) * 100, 1)

        return away_pct, home_pct

    except:
        return None, None


# -----------------------------
# FORMATO DE PITCHER
# -----------------------------
def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD (no confirmado)"

    era = p.get("era") or "N/A"
    whip = p.get("whip") or "N/A"

    return f"{p['name']} | ERA: {era} | WHIP: {whip}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()

    msg = "⚾ MLB ANALYST BOT ⚾\n\n"

    dates = data.get("dates", [])

    if not dates:
        msg += "No hay juegos hoy."
    else:
        for game in dates[0].get("games", []):
            game_pk = game.get("gamePk")

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            pitchers = get_probable_pitchers(game_pk)

            away = pitchers["away"] if pitchers else None
            home = pitchers["home"] if pitchers else None

            away_pct, home_pct = get_win_probability(away, home)

            msg += f"⚾ {away_team} vs {home_team}\n"
            msg += f"Pitcher Visitante: {format_pitcher(away)}\n"
            msg += f"Pitcher Local: {format_pitcher(home)}\n"

            if away_pct and home_pct:
                msg += "📊 Probabilidad de victoria:\n"
                msg += f"Visitante: {away_pct}%\n"
                msg += f"Local: {home_pct}%\n"
            else:
                msg += "📊 Probabilidad: Datos insuficientes\n"

            msg += "\n──────────────────\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

    print("OK")


if __name__ == "__main__":
    main()
