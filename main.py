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
                "status": game.get("status", {}).get("detailedState", "")
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
# MATCHING FIXED
# =========================

def match_games(mlb_games, odds_games):

    matched = []
    used_keys = set()

    for m in mlb_games:

        mlb_home = normalize_team(m["home_team"])
        mlb_away = normalize_team(m["away_team"])

        match_key = f"{mlb_home}_vs_{mlb_away}"

        best_match = None

        for o in odds_games:

            odds_home = normalize_team(o["home_team"])
            odds_away = normalize_team(o["away_team"])

            odds_key_1 = f"{odds_home}_vs_{odds_away}"
            odds_key_2 = f"{odds_away}_vs_{odds_home}"

            if match_key == odds_key_1 or match_key == odds_key_2:

                if match_key in used_keys:
                    continue

                best_match = o
                used_keys.add(match_key)
                break

        if best_match:

            matched.append({
                **m,
                "odds": best_match
            })

    return matched

# =========================
# CLASSIFY GAME (LIVE / PRE)
# =========================

def classify_game(game):

    try:

        game_time = datetime.fromisoformat(
            game["gameDate"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        now = datetime.now(timezone.utc)

        status = game.get("status", "").lower()

        # FINAL
        if "final" in status or "completed" in status:
            return None

        # LIVE
        if "in progress" in status or "live" in status:
            return "LIVE"

        # FUTURE (PRE-GAME)
        if game_time > now:
            return "PRE"

        return "LIVE"

    except Exception as e:
        print("CLASSIFY ERROR:", e)
        return None

# =========================
# SIMPLE MODEL
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
# MAIN
# =========================

def main():

    print("🚀 MLB V8 LIVE SYSTEM")

    mlb_games = get_mlb_games()
    odds_games = get_odds_games()

    games = match_games(mlb_games, odds_games)

    print("MLB:", len(mlb_games))
    print("MATCHED:", len(games))

    pre_report = "🟢 PRE-GAME PICKS\n\n"
    live_report = "🔴 LIVE BETTING\n\n"

    pre_count = 0
    live_count = 0

    for game in games:

        state = classify_game(game)

        if state is None:
            continue

        away = game["away_team"]
        home = game["home_team"]

        pick = pick_model(game)

        if state == "PRE":

            pre_count += 1

            pre_report += (
                f"⚾ {away} vs {home}\n"
                f"🏟 {game['away_pitcher']} vs {game['home_pitcher']}\n"
                f"🎯 Pick: {pick}\n\n"
                f"────────────────────\n\n"
            )

        else:

            live_count += 1

            live_report += (
                f"🔴 {away} vs {home} (LIVE)\n"
                f"🏟 {game['away_pitcher']} vs {game['home_pitcher']}\n"
                f"🎯 Pick: {pick}\n\n"
                f"────────────────────\n\n"
            )

    final_msg = (
        f"📊 MLB V8 LIVE SYSTEM\n"
        f"🟢 PRE: {pre_count}\n"
        f"🔴 LIVE: {live_count}\n\n"
        + pre_report + "\n" + live_report
    )

    send(final_msg)

    print("✅ Enviado a Telegram")

if __name__ == "__main__":
    main()
