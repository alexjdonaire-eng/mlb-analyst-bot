import os
import requests
import pandas as pd

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
            return 0, 0

        stat = stats[0]["splits"][0]["stat"]
        return float(stat.get("era", 0)), float(stat.get("whip", 0))

    except:
        return 0, 0


# -----------------------------
# PROBABLE PITCHERS
# -----------------------------
def get_pitchers(game_pk):
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


# -----------------------------
# OFFENSE METRIC
# -----------------------------
def get_offense():
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


# -----------------------------
# MODEL
# -----------------------------
def model(away, home, offense, away_team, home_team):

    a = 50
    h = 50

    # pitching
    a += (home["era"] - away["era"]) * 9
    h -= (home["era"] - away["era"]) * 9

    a += (home["whip"] - away["whip"]) * 6
    h -= (home["whip"] - away["whip"]) * 6

    # offense
    if away_team in offense and home_team in offense:
        diff = offense[away_team] - offense[home_team]
        a += diff * 7
        h -= diff * 7

    total = a + h

    return round(a / total * 100, 1), round(h / total * 100, 1)


# -----------------------------
# EDGE (CLV PROXY)
# -----------------------------
def edge(diff):
    if diff >= 15:
        return "🟢 Ventaja fuerte"
    elif diff >= 9:
        return "🟡 Ventaja media"
    elif diff >= 6:
        return "⚪ Ventaja leve"
    return None


# -----------------------------
# STAKE SIMPLE
# -----------------------------
def stake(diff):
    if diff >= 15:
        return "💰💰💰 Alta"
    elif diff >= 9:
        return "💰💰 Media"
    elif diff >= 6:
        return "💰 Baja"
    return None


# -----------------------------
# PICK
# -----------------------------
def pick(a, h):
    return "Visitante" if a > h else "Local"


# -----------------------------
# BACKTEST ENGINE (simple)
# -----------------------------
def backtest_model(games, offense):

    results = []

    for g in games:

        try:
            pk = g["gamePk"]
            away_team = g["teams"]["away"]["team"]["name"]
            home_team = g["teams"]["home"]["team"]["name"]

            pitchers = get_pitchers(pk)
            if not pitchers:
                continue

            away_id = pitchers["away"]["id"]
            home_id = pitchers["home"]["id"]

            away_stats = {"era": 0, "whip": 0}
            home_stats = {"era": 0, "whip": 0}

            if away_id:
                away_stats["era"], away_stats["whip"] = get_pitcher_stats(away_id)

            if home_id:
                home_stats["era"], home_stats["whip"] = get_pitcher_stats(home_id)

            a, h = model(away_stats, home_stats, offense, away_team, home_team)

            diff = abs(a - h)

            if diff < 6:
                continue

            pick_side = pick(a, h)

            # resultado real
            result = g["teams"]["away"]["score"] > g["teams"]["home"]["score"]
            real = "Visitante" if result else "Local"

            win = pick_side == real

            results.append({
                "pick": pick_side,
                "diff": diff,
                "win": win
            })

        except:
            continue

    df = pd.DataFrame(results)

    if df.empty:
        return

    roi = df["win"].sum() - (len(df) - df["win"].sum())
    win_rate = df["win"].mean() * 100

    print("\n📊 BACKTEST RESULTADOS")
    print(f"ROI: {roi}")
    print(f"Win rate: {win_rate:.2f}%")
    print(df.head())


# -----------------------------
# LIVE BOT
# -----------------------------
def main():

    data = requests.get(SCHEDULE_URL, timeout=10).json()
    offense = get_offense()

    games = data.get("dates", [])[0].get("games", [])

    for g in games:

        pk = g["gamePk"]

        away_team = g["teams"]["away"]["team"]["name"]
        home_team = g["teams"]["home"]["team"]["name"]

        pitchers = get_pitchers(pk)
        if not pitchers:
            continue

        away = pitchers["away"]
        home = pitchers["home"]

        away_stats = {"era": 0, "whip": 0}
        home_stats = {"era": 0, "whip": 0}

        if away["id"]:
            away_stats["era"], away_stats["whip"] = get_pitcher_stats(away["id"])

        if home["id"]:
            home_stats["era"], home_stats["whip"] = get_pitcher_stats(home["id"])

        a, h = model(away_stats, home_stats, offense, away_team, home_team)

        diff = abs(a - h)

        e = edge(diff)
        s = stake(diff)

        if not e:
            continue

        msg = f"""⚾ MLB QUANT SYSTEM ⚾

{away_team} vs {home_team}

📊 Probabilidad:
Visitante: {a}%
Local: {h}%

📈 {e}
📌 Pick: {pick(a,h)}
{s if s else ""}

──────────────────
"""

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )

        print(f"Sent: {away_team} vs {home_team}")


if __name__ == "__main__":

    # LIVE MODE
    main()

    # BACKTEST MODE (opcional manual)
    # data = requests.get(SCHEDULE_URL).json()
    # backtest_model(data.get("dates",[0]).get("games",[]), get_offense())
