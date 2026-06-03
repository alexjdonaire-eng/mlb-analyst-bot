import json
import traceback
import requests

HISTORY_FILE = "market_history.jsonl"

# =========================
# TELEGRAM
# =========================
def send(msg, token, chat_id):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
            timeout=20
        )
    except Exception as e:
        print("❌ Telegram error:", e)


# =========================
# DATA
# =========================
def load_history():
    rows = []
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    except:
        pass
    return rows


def latest_games(history):
    games = {}
    for r in reversed(history):
        key = f"{r.get('away_team')}_{r.get('home_team')}"
        if key not in games:
            games[key] = r
    return list(games.values())


# =========================
# MARKET MATH (SEMI PRO CORE)
# =========================
def implied_probs(odds):
    return {k: (1 / v) for k, v in odds.items()}


def remove_vig(probs):
    total = sum(probs.values())
    return {k: v / total for k, v in probs.items()}


# =========================
# FILTER GAME QUALITY
# =========================
def valid_game(game):
    odds = game.get("odds", {})

    if len(odds) < 2:
        return False

    values = list(odds.values())

    if min(values) < 1.05:
        return False

    if max(values) - min(values) < 0.15:
        return False

    return True


# =========================
# VALUE ENGINE
# =========================
def find_value_bet(odds):

    probs = implied_probs(odds)
    probs = remove_vig(probs)

    best_team = max(probs, key=probs.get)
    best_prob = probs[best_team]

    # 🔥 SEMI-PRO RULES
    if best_prob < 0.57:
        return None

    if best_prob > 0.78:
        return None

    edge = best_prob - 0.5

    return {
        "team": best_team,
        "prob": round(best_prob * 100, 2),
        "edge": round(edge * 100, 2)
    }


# =========================
# CONFIDENCE SCORING
# =========================
def confidence(prob):

    if prob >= 0.66:
        return "🔥 HIGH VALUE"
    elif prob >= 0.60:
        return "✅ MEDIUM VALUE"
    else:
        return "⚠️ LOW EDGE"


# =========================
# MAIN ANALYZER
# =========================
def main():

    import os

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    history = load_history()
    games = latest_games(history)

    report = "🏦 MLB SEMI-PRO BETTING BOT\n\n"
    total = 0

    for g in games:

        try:
            if not valid_game(g):
                continue

            odds = g.get("odds", {})
            result = find_value_bet(odds)

            if not result:
                continue

            status = confidence(result["prob"])

            report += (
                f"⚾ {g.get('away_team')} vs {g.get('home_team')}\n"
                f"🎯 Pick: {result['team']}\n"
                f"📊 Probability: {result['prob']}%\n"
                f"📈 Edge: {result['edge']}%\n"
                f"🏷 Status: {status}\n\n"
                f"----------------------\n\n"
            )

            total += 1

        except Exception as e:
            print("❌ Game error:", e)
            traceback.print_exc()

    if total == 0:
        report = "🏦 MLB SEMI-PRO BETTING BOT\n\n⚠️ No value bets found today."

    print(report)
    send(report, TOKEN, CHAT_ID)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
