import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ El bot está funcionando")

def main():

    print("🚀 INICIANDO BOT")
    print("TOKEN CARGADO:", bool(TOKEN))

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("✅ BOT LISTO")

    app.run_polling()

if __name__ == "__main__":
    main()
