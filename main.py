import os
import requests
from analyzer import analyze_games

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

def fetch_games():
    params = {
        "apiKey": os.getenv("ODDS_API_KEY"),
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }

    r = requests.get(URL, params=params, timeout=20)
    data = r.json()

    if not isinstance(data, list):
        return []

    return data


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })


def format_game(g):
    return f"""
⚾ {g['home']} vs {g['away']}

🧾 Lanzadores
{g['home']}: {g['home_pitcher']['name']} (ERA {g['home_pitcher']['era']} | WHIP {g['home_pitcher']['whip']})
{g['away']}: {g['away_pitcher']['name']} (ERA {g['away_pitcher']['era']} | WHIP {g['away_pitcher']['whip'])}

🎯 Ganador: {g['winner']} ({g['confidence']}%)

⚾ Total: {g['total_type']} {g['total']}
⚾ Hándicap: {g['spread_team']} -1.5

📊 Confianza: {g['confidence']}%
🏷 Nivel: {g['level']}
💎 Jugada: {g['recommendation']}

━━━━━━━━━━━━━━
"""


def main():
    games = fetch_games()

    if not games:
        send("⚠️ No hay juegos hoy o error API")
        return

    analyzed = analyze_games(games)

    # 🔥 IMPORTANTÍSIMO: evitar spam + duplicados
    sent = set()

    batch = []

    for g in analyzed:
        key = f"{g['home']}vs{g['away']}"
        if key in sent:
            continue
        sent.add(key)

        batch.append(format_game(g))

        if len(batch) == 3:
            send("\n".join(batch))
            batch = []

    if batch:
        send("\n".join(batch))

    # TOP PICKS LIMPIO
    top = sorted(analyzed, key=lambda x: x["confidence"], reverse=True)[:5]

    top_msg = "🔥 TOP PICKS DEL DÍA\n\n"
    for i, g in enumerate(top, 1):
        top_msg += f"{i}. {g['winner']} ({g['confidence']}%)\n"

    send(top_msg)


if __name__ == "__main__":
    main()
