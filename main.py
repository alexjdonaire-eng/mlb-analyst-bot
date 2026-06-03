import time
import traceback

from collector import main as collector_main
from analyzer import main as analyzer_main

SLEEP_SECONDS = 60  # ajusta si quieres más/menos frecuencia


def run_cycle():
    print("\n==============================")
    print("🚀 NEW CYCLE STARTING")
    print("==============================\n")

    # -------------------------
    # COLLECTOR
    # -------------------------
    try:
        print("📡 Running collector...")
        collector_main()
        print("✅ Collector OK\n")

    except Exception as e:
        print("❌ Collector error:")
        print(str(e))
        traceback.print_exc()

    # -------------------------
    # ANALYZER
    # -------------------------
    try:
        print("🧠 Running analyzer...")
        analyzer_main()
        print("✅ Analyzer OK\n")

    except Exception as e:
        print("❌ Analyzer error:")
        print(str(e))
        traceback.print_exc()

    print("🏁 CYCLE FINISHED")


# =========================
# MAIN LOOP (EVITA STOP CONTAINER)
# =========================
if __name__ == "__main__":

    print("🔥 BOT STARTED - RAILWAY LIVE MODE")

    while True:
        try:
            run_cycle()

        except Exception as e:
            print("🔥 CRITICAL ERROR (loop protected):")
            print(str(e))
            traceback.print_exc()

        print(f"⏱️ Sleeping {SLEEP_SECONDS} seconds...\n")
        time.sleep(SLEEP_SECONDS)
