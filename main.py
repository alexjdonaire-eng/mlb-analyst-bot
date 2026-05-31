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
            "away": {"name": away.get("fullName"), "era": away_era, "whip": away_whip},
            "home": {"name": home.get("fullName"), "era": home_era, "whip": home_whip}
        }

    except:
        return None


# -----------------------------
# MODELO CUANTITATIVO BASE
# -----------------------------
def model_probability(away, home):
    away_score = 50
    home_score = 50

    if not away or not home:
        return None, None

    # ERA
    if away["era"] and home["era"]:
        diff = float(home["era"]) - float(away["era"])
        away_score += diff * 9
        home_score -= diff * 9

    # WHIP
    if away["whip"] and home["whip"]:
        diff = float(home["whip"]) - float(away["whip"])
        away_score += diff * 6
        home_score -= diff * 6

    total = away_score + home_score

    return (
        (away_score / total) * 100,
        (home_score / total) * 100
    )


# -----------------------------
# EDGE HEDGE FUND
# -----------------------------
def classify_play(away_pct, home_pct):
    diff = abs(away_pct - home_pct)

    if diff < 8:
        return "NO BET", 0, diff

    if diff >= 15:
        return "🟢 STRONG PLAY", 3, diff
    elif diff >= 11:
        return "🟡 LEAN", 2, diff
    else:
        return "🟡 LEAN", 1, diff


# -----------------------------
# PICK
# -----------------------------
def get_pick(away_pct, home_pct):
    return "Visitante" if away_pct > home_pct else "Local"


# -----------------------------
# FORMAT
# -----------------------------
def format_pitcher(p):
    if not p or not p.get("name"):
        return "TBD"
    return f"{p['name']} | ERA {p['era'] or 'N/A'} | WHIP {p['whip'] or 'N/A'}"


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = requests.get(SCHEDULE_URL, timeout=10).json()

    dates = data.get("dates", [])

    if not dates:
        return

    for game in dates[0].get("games", []):

        game_pk = game.get("gamePk")

        away_team = game["teams"]["away"]["team"]["name"]
        home_team = game["teams"]["home"]["team"]["name"]

        pitchers = get_probable_pitchers(game_pk)

        away = pitchers["away"] if pitchers else None
        home = pitchers["home"] if pitchers else None

        away_pct, home_pct = model_probability(away, home)

        if not away_pct:
            continue

        label, stake, diff = classify_play(away_pct, home_pct)

        # FILTRO HEDGE FUND (solo valor real)
        if label == "NO BET":
            continue

        pick_side = get_pick(away_pct, home_pct)

        msg = f"""🏦 MLB HEDGE FUND MODEL 🏦

{away_team} vs {home_team}

Pitcher Visitante: {format_pitcher(away)}
Pitcher Local: {format_pitcher(home)}

📊 Probabilidad:
Visitante: {round(away_pct,1)}%
Local: {round(home_pct,1)}%

📈 Clasificación: {label}
📌 Pick: {pick_side}
💰 Stake: {stake}u

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
