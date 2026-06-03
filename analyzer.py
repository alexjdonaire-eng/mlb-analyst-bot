import os
import json
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MEM_FILE = "memory_store.json"


# =========================
# TELEGRAM
# =========================
def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


# =========================
# MEMORY
# =========================
def load_memory():
    try:
        with open(MEM_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "wins": [],
            "losses": [],
            "prob_bins": {
                "55-60": {"wins": 0, "losses": 0},
                "60-70": {"wins": 0, "losses": 0}
            }
        }


def save_memory(mem):
    with open(MEM_FILE, "w") as f:
        json.dump(mem, f)


# =========================
# STEAM DETECTION (simple but real)
# =========================
def detect_steam(prev_probs, current_probs):
    steam_score = 0

    for team in current_probs:
        if team in prev_probs:
            delta = current_probs[team] - prev_probs[team]

            # movimiento fuerte del mercado
            if delta > 2.0:
                steam_score += 1
            elif delta > 4.0:
                steam_score += 2

    return steam_score


# =========================
# PROBABILITY IMPROVER (memory bias)
# =========================
def adjust_by_memory(prob, mem):
    if 55 <= prob < 60:
        stats = mem["prob_bins"]["55-60"]
    elif 60 <= prob < 70:
        stats = mem["prob_bins"]["60-70"]
    else:
        return prob

    total = stats["wins"] + stats["losses"]

    if total == 0:
        return prob

    winrate = stats["wins"] / total

    # ajuste leve
    return prob * (0.95 + winrate * 0.1)


# =========================
# PARLAY BUILDER
# =========================
def build_parlay(picks):
    # orden por estabilidad
    picks = sorted(picks, key=lambda x: x["final_score"], reverse=True)

    parlay = []
    used_teams = set()

    for p in picks:
        game = p["game"]

        # evitar correlación simple (mismo equipo repetido)
        if game in used_teams:
            continue

        if p["prob"] < 57:
            continue

        parlay.append(p)
        used_teams.add(game)

        if len(parlay) == 4:
            break

    return parlay


# =========================
# MAIN CORE
# =========================
def run(games, prev_snapshot=None):

    mem = load_memory()

    picks = []

    for g in games:

        odds = g["odds"]
        if len(odds) < 2:
            continue

        teams = list(odds.keys())

        # implied prob
        p1 = (1 / odds[teams[0]]) * 100
        p2 = (1 / odds[teams[1]]) * 100

        current_probs = {
            teams[0]: p1,
            teams[1]: p2
        }

        # steam detection
        steam = 0
        if prev_snapshot:
            steam = detect_steam(prev_snapshot.get(g["game_id"], {}), current_probs)

        fav = max(current_probs, key=current_probs.get)
        prob = current_probs[fav]

        # memory adjustment
        prob_adj = adjust_by_memory(prob, mem)

        final_score = prob_adj + steam * 2

        picks.append({
            "game": f"{g['away']} vs {g['home']}",
            "pick": fav,
            "prob": round(prob_adj, 2),
            "steam": steam,
            "final_score": final_score
        })

    # =========================
    # PARLAY OPTIMIZER
    # =========================
    parlay = build_parlay(picks)

    # =========================
    # TELEGRAM OUTPUT CLEAN
    # =========================
    msg = "🏦 SHARP MONEY V7 — STEAM + MEMORY + PARLAY\n\n"

    for p in picks:
        msg += (
            f"⚾ {p['game']}\n"
            f"🎯 Pick: {p['pick']}\n"
            f"📊 Prob: {p['prob']}%\n"
            f"🔥 Steam: {p['steam']}\n\n"
            "━━━━━━━━━━━━━━\n"
        )

    msg += "\n🏦 COMBINADA OPTIMIZADA\n\n"

    for p in parlay:
        msg += f"• {p['pick']} ({p['game']})\n"

    msg += "\n⚠️ Ajustada por steam + memoria + estabilidad"

    send(msg)

    print("V7 SENT")

    return picks, parlay
