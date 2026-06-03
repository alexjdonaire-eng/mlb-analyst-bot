from grader import grade_picks
from tracker import daily_report
import requests
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )

print("📊 CALIFICANDO PICKS")

grade_picks()

report = daily_report()

send_telegram(report)

print("✅ REPORTE ENVIADO")
