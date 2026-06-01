def main():

    print("🚀 INICIANDO BOT")
    print("TOKEN CARGADO:", bool(TOKEN))

    try:
        print("PASO 1")

        app = Application.builder().token(TOKEN).build()

        print("PASO 2")

        app.add_handler(CommandHandler("start", start))

        print("PASO 3")

        app.run_polling()

    except Exception as e:
        print("ERROR:", repr(e))
