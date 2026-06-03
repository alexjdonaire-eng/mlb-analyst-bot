import time
import os

from collector import main as run_collector
from analyzer import main as run_analyzer

print("🔥 BOT PRO V2 STARTED")

while True:
    try:
        print("\n====================")
        print("🚀 NEW CYCLE")
        print("====================")

        print("📡 Collector...")
        run_collector()

        print("🧠 Analyzer...")
        run_analyzer()

        print("⏳ Sleeping 60s...")
        time.sleep(60)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(10)
