import os
import requests

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("8916331113:AAF_ffi01DlYqTSVqAJGqiJTVLKnMHzbe70")
CHAT_ID = os.getenv("5163780989")

print("🚀 BOT INICIANDO")
print("TOKEN CARGADO:", TOKEN is not None)
print("CHAT_ID CARGADO:", CHAT_ID is not None)

# =========================
# TELEGRAM
# =========================
def send_message(text):
    if not TOKEN:
        print("❌ Falta TELEGRAM_BOT_TOKEN")
        return

    if not CHAT_ID:
        print("❌ Falta TELEGRAM_CHAT_ID")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("RESPUESTA:", response.text)

    except Exception as e:
        print("ERROR:", e)

# =========================
# TEST
# =========================
if __name__ == "__main__":

    send_message(
        "✅ TEST RAILWAY OK\n\nSi recibes este mensaje, Telegram está conectado correctamente."
    )
