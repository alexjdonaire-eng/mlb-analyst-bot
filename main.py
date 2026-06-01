import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# =========================
# MLB
# =========================

def obtener_juegos_mlb():
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
        r = requests.get(url, timeout=20)

        if r.status_code != 200:
            return ["No se pudieron obtener los juegos MLB."]

        data = r.json()

        juegos = []

        for fecha in data.get("dates", []):
            for game in fecha.get("games", []):

                visitante = game["teams"]["away"]["team"]["name"]
                local = game["teams"]["home"]["team"]["name"]

                juegos.append(
                    f"⚾ {visitante} vs {local}"
                )

        if not juegos:
            juegos.append("No hay juegos MLB programados hoy.")

        return juegos

    except Exception as e:
        return [f"Error MLB: {e}"]

# =========================
# COMANDOS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al MLB Bot.\n\n"
        "Comandos disponibles:\n"
        "/mlb - Juegos MLB del día\n"
        "/status - Estado del bot"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot activo y funcionando."
    )

async def mlb(update: Update, context: ContextTypes.DEFAULT_TYPE):

    juegos = obtener_juegos_mlb()

    for juego in juegos:
        await update.message.reply_text(juego)

# =========================
# MAIN
# =========================

def main():

    print("🚀 BOT INICIADO")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("mlb", mlb))

    app.run_polling()

if __name__ == "__main__":
    main()
