import hashlib

# =========================
# ANALYZER V9 PRO
# =========================

def analyze_games(games):
    results = []
    seen = set()

    for g in games:
        home = g.get("home_team")
        away = g.get("away_team")

        if not home or not away:
            continue

        key = f"{away}_vs_{home}"

        # 🚫 evitar duplicados
        if key in seen:
            continue
        seen.add(key)

        # =========================
        # PITCHERS (MLB no siempre los da)
        # =========================
        home_pitcher = {
            "name": "TBD",
            "era": "-",
            "whip": "-"
        }

        away_pitcher = {
            "name": "TBD",
            "era": "-",
            "whip": "-"
        }

        # =========================
        # PROBABILIDAD ESTABLE (sin API random)
        # =========================
        h_seed = int(hashlib.md5(home.encode()).hexdigest(), 16)
        a_seed = int(hashlib.md5(away.encode()).hexdigest(), 16)

        home_prob = 45 + (h_seed % 25)
        away_prob = 45 + (a_seed % 25)

        winner = home if home_prob > away_prob else away
        confidence = round(max(home_prob, away_prob), 2)

        # =========================
        # TOTAL (over/under dinámico)
        # =========================
        base_total = 8.0 + ((h_seed + a_seed) % 20) / 10
        total = round(base_total, 1)

        total_type = "Alta" if confidence >= 52 else "Baja"

        # =========================
        # HANDICAP
        # =========================
        spread_team = winner

        # =========================
        # NIVEL
        # =========================
        if confidence >= 70:
            level = "🔥 ELITE"
        elif confidence >= 60:
            level = "✅ FUERTE"
        elif confidence >= 52:
            level = "⚠️ LEAN"
        else:
            level = "🚫 PASAR"

        recommendation = winner if confidence >= 52 else "NO JUGAR"

        # =========================
        # OUTPUT STRUCTURE
        # =========================
        results.append({
            "home": home,
            "away": away,

            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,

            "winner": winner,
            "confidence": confidence,

            "total": total,
            "total_type": total_type,

            "spread_team": spread_team,

            "level": level,
            "recommendation": recommendation
        })

    return results
