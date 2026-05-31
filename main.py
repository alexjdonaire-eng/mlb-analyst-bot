import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


# -----------------------------
# STATS DEL PITCHER (ERA / WHIP)
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
