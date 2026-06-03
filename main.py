import os
import requests
from analyzer import analyze_games, top_picks

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ---------- FETCH MLB GAMES ----------
def fetch_mlb_games():
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
    res = requests.get(url, timeout=15)
    data = res.json()
    games_list = []

    for date in data.get("dates", []):
        for g in date.get("games", []):
            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]

            games_list.append({
                "home": home,
                "away": away,
                "winner": home,  # placeholder, luego calculas con tu modelo
                "winner_pct": 75, # ejemplo
                "total_value": 9.5,
                "total_type": "Alta",
                "total_pct": 70,
                "handicap_value": -1.5,
                "handicap_team": home,
                "handicap_pct": 65
            })

    return games_list

# ---------- SEND TO TELEGRAM ----------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# ---------- MAIN ----------
def main():
    games = fetch_mlb_games()
    analyzed = analyze_games(games)
    top_winners, top_totals, top_handicaps = top_picks(analyzed)

    # Mensajes compactos
    for game in analyzed:
        msg = f"⚾ {game['match']}\n\n"
        msg += f"🧾 Lanzadores\n"
        msg += f"{game['home_pitcher']['name']}: ERA {game['home_pitcher']['ERA']} | WHIP {game['home_pitcher']['WHIP']}\n"
        msg += f"{game['away_pitcher']['name']}: ERA {game['away_pitcher']['ERA']} | WHIP {game['away_pitcher']['WHIP']}\n\n"
        msg += f"🎯 Ganador: {game['winner']} ({game['winner_pct']}%)\n"
        msg += f"⚾ Total: {game['total_type']} {game['total']} {game['total_pct']}%\n"
        msg += f"⚾ Hándicap: {game['handicap']} {game['handicap_team']} {game['handicap_pct']}%\n\n"
        msg += f"📊 Confianza: {game['confidence']}%\n"
        msg += f"🏷 Nivel: {game['level']}\n"
        msg += f"💎 Jugada recomendada: {game['recommended']}\n"
        send_telegram(msg)

    # Top picks separados
    msg = "🔥 TOP PICKS DEL DÍA\n\n*Ganadores:*\n"
    for g in top_winners:
        msg += f"{g['winner']} gana ({g['winner_pct']}%)\n"
    msg += "\n*Totales:*\n"
    for g in top_totals:
        msg += f"{g['match']} {g['total_type']} {g['total']} ({g['total_pct']}%)\n"
    msg += "\n*Hándicaps:*\n"
    for g in top_handicaps:
        msg += f"{g['match']} {g['handicap']} {g['handicap_team']} ({g['handicap_pct']}%)\n"

    send_telegram(msg)

if __name__ == "__main__":
    main()
