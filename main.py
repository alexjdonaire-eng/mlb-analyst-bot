import time
import traceback
from collector import main as collector_main
from analyzer import main as analyzer_main

# =========================
# CONFIG
# =========================
SLEEP_SECONDS = 60  # cada cuánto corre el ciclo (ajústalo si quieres)

# =========================
# LOOP PRINCIPAL
# =========================
def run_cycle():

    print("\n==============================")
    print("🚀 NEW CYCLE STARTING")
    print("==============================\n")

    # 1. COLLECTOR
    try:
        print("📡 Running collector...")
        collector_main()
        print("✅ Collector finished\n")

    except Exception as e:
        print("❌ Collector error:")
        print(str(e))
        traceback.print_exc()

    # 2. ANALYZER
    try:
        print("🧠 Running analyzer...")
        analyzer_main()
        print("✅ Analyzer finished\n")

    except Exception as e:
        print("❌ Analyzer error:")
        print(str(e))
        traceback.print_exc()

    print("🏁 Cycle completed")


# =========================
# MAIN LOOP (24/7)
# =========================
if __name__ == "__main__":

    print("🚀 BOT STARTED (PRODUCTION MODE)")

    while True:

        try:
            run_cycle()

        except Exception as e:
            print("🔥 CRITICAL LOOP ERROR:")
            print(str(e))
            traceback.print_exc()

        print(f"⏱️ Sleeping {SLEEP_SECONDS} seconds...\n")
        time.sleep(SLEEP_SECONDS)
