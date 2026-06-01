import os
import requests
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

STATE_FILE = "estado.json"


def enviar_mensaje(texto):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": texto}
    )


def cargar_estado():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def guardar_estado(estado):
    with open(STATE_FILE, "w") as f:
        json.dump(estado, f)


def probabilidad(odds):
    return 1 / odds


def quitar_margen(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total


def main():

    estado = cargar_estado()

    parametros = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    respuesta = requests.get(URL, params=parametros)

    if respuesta.status_code != 200:
        enviar_mensaje("❌ Error conectando a cuotas")
        return

    juegos = respuesta.json()

    for juego in juegos:

        equipo_local = juego["home_team"]
        equipo_visitante = juego["away_team"]
        id_juego = juego.get("id", equipo_local + "_" + equipo_visitante)

        libro = juego["bookmakers"][0]
        resultados = libro["markets"][0]["outcomes"]

        cuota_local = None
        cuota_visitante = None

        for r in resultados:
            if r["name"] == equipo_local:
                cuota_local = r["price"]
            if r["name"] == equipo_visitante:
                cuota_visitante = r["price"]

        if not cuota_local or not cuota_visitante:
            continue

        p_local = probabilidad(cuota_local)
        p_visitante = probabilidad(cuota_visitante)

        p_local, p_visitante = quitar_margen(p_local, p_visitante)

        favorito = equipo_local if p_local > p_visitante else equipo_visitante

        prob_favorito = max(p_local, p_visitante)

        # guardar apertura
        if id_juego not in estado:
            estado[id_juego] = {
                "apertura_local": cuota_local,
                "apertura_visitante": cuota_visitante
            }

        # CLV real
        apertura = estado[id_juego]["apertura_local"]
        cierre = cuota_local

        clv = (1 / cierre) - (1 / apertura)

        diferencia = abs(p_local - p_visitante)

        # FILTRO DE APUESTA
        hay_apuesta = (
            clv > 0.01 and
            diferencia > 0.03
        )

        if hay_apuesta:

            mensaje = f"""
🏦 SEÑAL DE APUESTA MLB

⚾ {equipo_visitante} vs {equipo_local}

📊 Favorito: {favorito}

📈 Probabilidad:
Local: {round(p_local*100,2)}%
Visitante: {round(p_visitante*100,2)}%

📊 Mejora de valor (CLV): {round(clv*100,2)}%

🔥 DECISIÓN: APUESTA POSIBLE
"""

            enviar_mensaje(mensaje)

        else:

            print(f"Sin valor: {equipo_visitante} vs {equipo_local}")

    guardar_estado(estado)


if __name__ == "__main__":
    main()
