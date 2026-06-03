# main.py
import os
import requests
from analyzer import analyze_games

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher,team"
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_pitcher_stats(player_id):
    if not player_id:
        return {"name": "TBD", "ERA": "-", "WHIP": "-"}
    try:
        res = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching", timeout=15)
        data = res.json()
        stats = data["stats"][0]["splits"][0]["stat"]
        return {"name": "", "ERA": stats.get("era", "-"), "WHIP": stats.get("whip", "-")}
    except:
        return {"name": "TBD", "ERA": "-", "WHIP": "-"}

def fetch_mlb_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, timeout=20)
        data = res.json()
    except:
        return []
    
    games = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            try:
                home = g["teams"]["home"]["team"]["name"]
                away = g["teams"]["away"]["team"]["name"]
                hp = g["teams"]["home"].get("probablePitcher", {})
                ap = g["teams"]["away"].get("probablePitcher", {})
                
                home_pitcher = {"name": hp.get("fullName", "TBD"), **fetch_pitcher_stats(hp.get("id"))}
                away_pitcher = {"name": ap.get("fullName", "TBD"), **fetch_pitcher_stats(ap.get("id"))}
                
                games.append({
                    "home_team": home,
                    "away_team": away,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher
                })
            except:
                continue
    return games

def format_game(game):
    home = game["home_team"]
    away = game["away_team"]
    home_pitcher = game["home_pitcher"]
    away_pitcher = game["away_pitcher"]
    winner = game["predicted_winner"]
    total = game["predicted_total"]
    handicap = game["predicted_handicap"]
    pick_type = game["top_pick_type"]
    pick_value = game["top_pick_value"]
    
    return (
f"⚾ {away} vs {home}\n\n"
f"🧾 Lanzadores\n"
f"{away}: {away_pitcher['name']} (ERA {away_pitcher['ERA']} | WHIP {away_pitcher['WHIP']})\n"
f"{home}: {home_pitcher['name']} (ERA {home_pitcher['ERA']} | WHIP {home_pitcher['WHIP']})\n\n"
f"🎯 Ganador: {winner.get('team', 'TBD')} ({winner.get('prob', 0)}%)\n"
f"⚾ Total: {total.get('line', '-')} ({total.get('prob', 0)}%)\n"
f"⚾ Hándicap: {handicap.get('line', '-')} ({handicap.get('prob', 0)}%)\n\n"
f"📊 Confianza: {game.get('confidence', 0)}%\n"
f"🏷 Nivel: {game.get('level', '🚫 PASAR')}\n"
f"💎 Jugada: {pick_type} → {pick_value}"
    )

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    games = fetch_mlb_games()
    if not games:
        send_telegram_message("⚠️ No hay juegos hoy o error al obtener datos.")
        return
    
    analyzed = analyze_games(games)
    
    for g in analyzed:
        msg = format_game(g)
        send_telegram_message(msg)
    
    top5 = sorted(analyzed, key=lambda x: x.get("confidence", 0), reverse=True)[:5]
    top_msg = "🔥 TOP 5 PICKS DEL DÍA\n\n"
    for t in top5:
        top_msg += f"{t['top_pick_type']} → {t['top_pick_value']} ({t['confidence']}%)\n"
    send_telegram_message(top_msg)

if __name__ == "__main__":
    main()
