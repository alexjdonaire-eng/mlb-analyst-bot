import os
import requests
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_URL = "https://statsapi.mlb.com/api/v1/schedule"

# =========================
# TELEGRAM
# =========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

# =========================
# NORMALIZER
# =========================

def normalize_team(name):
    return (
        name.lower()
        .replace("new york", "ny")
        .replace("los angeles", "la")
        .replace("st. louis", "st louis")
        .replace(" ", "")
    )

# =========================
# MLB GAMES
# =========================

def get_mlb_games():

    today = datetime.now().strftime("%Y-%m-%d")

    url = f"{MLB_URL}?sportId=1&date={today}&hydrate=probablePitcher"
    r = requests.get(url)

    if r.status_code != 200:
        print("ERROR MLB:", r.text)
        return []

    data = r.json()
    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):

            games.append({
                "id": game.get("gamePk"),
                "gameDate": game.get("gameDate"),
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "away_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName") or "UNKNOWN",
                "status": game.get("status", {}).get("detailedState")
            })

    return games

# =========================
# ODDS API
# =========================

def get_odds_games():

    r = requests.get(
        ODDS_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    if r.status_code != 200:
        print("ERROR ODDS:", r.text)
        return []

    return r.json()

# =========================
# MATCHING FIXED (NO DUPLICATES)
# =========================

def match_games(mlb_games, odds_games):

    matched = []
    used_odds = set()

    for m in mlb_games:

        mlb_home = normalize_team(m["home_team"])
        mlb_away = normalize_team(m["away_team"])

        best_match = None
        best_index = None

        for i, o in enumerate(odds_games):

            if i in used_odds:
                continue

            odds_home = normalize_team(o["home_team"])
            odds_away = normalize_team(o["away_team"])

            if (
                (mlb_home == odds_home and mlb_away == odds_away)
                or
                (mlb_home == odds_away and mlb_away == odds_home)
            ):
                best_match = o
                best_index = i
                break

        if best_match:

            used_odds.add(best_index)

            matched.append({
                **m,
                "odds": best_match
            })

    return matched

# =========================
# MODEL SIMPLE
# =========================

def pick_model(game):

    try:

        book = game["odds"]["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]

        home = game["home_team"]
        away = game["away_team"]

        home_odds = None
        away_odds = None

        for o in outcomes:

            if o["name"] == home:
                home_odds = o["price"]

            if o["name"] == away:
                away_odds = o["price"]

        if home_odds and away_odds:

            if home_odds <= away_odds:
                return home
            else:
                return away

    except Exception as e:
        print("MODEL ERROR:", e)

    return game["home_team"]

# =========================
# FILTER TODAY
# =========================

def is_today(game):

    try:
        game_date = datetime.fromisoformat(
            game["gameDate"].replace("Z", "+00:00")
        ).date()

        today = datetime.now(timezone.utc).date()

        return game_date == today

    except Exception as e:
        print("DATE ERROR:", e)
        return False

# =========================
# MAIN
# =========================

def main():

    print("🚀 MLB V8 FIXED SYSTEM")

    mlb_games = get_mlb_games()
    odds_games = get_odds_games()

    games = match_games(mlb_games, odds_games)

    print("MLB GAMES:", len(mlb_games))
    print("MATCHED GAMES:", len(games))

    report = "🏦 MLB QUANT V8 FIXED\n\n"

    total = 0
    seen = set()

    for game in games:

        if not is_today(game):
            continue

        game_id = game.get("id")

        if game_id in seen:
            continue

        seen.add(game_id)

        away = game["away_team"]
        home = game["home_team"]

        pick = pick_model(game)

        total += 1

        report += (
            f"⚾ {away} vs {home}\n"
            f"🏟 Pitchers: {game['away_pitcher']} vs {game['home_pitcher']}\n"
            f"🎯 Pick: {pick}\n\n"
            f"────────────────────\n\n"
        )

    report = f"📊 Juegos analizados: {total}\n\n" + report

    send(report)

    print("✅ Enviado a Telegram")

if __name__ == "__main__":
    main()
