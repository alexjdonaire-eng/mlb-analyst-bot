def main():
    print("TOKEN =", TOKEN)

    if not TOKEN:
        print("ERROR: TOKEN VACIO")
        return

    app = Application.builder().token(TOKEN).build()

    print("BOT CREADO CORRECTAMENTE")

    app.run_polling()
