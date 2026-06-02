import time
from collector import run_collector
from analyzer import run_analyzer

print("🚀 BOT STARTED")

while True:
    try:
        run_collector()
        run_analyzer()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(60)
