import time
from collector import main as collector_main
from analyzer import main as analyzer_main

print("🚀 PRO BOT CYCLE START")

start = time.time()

# =========================
# COLLECTOR
# =========================
try:
    print("📡 Running collector...")
    collector_main()
    print("✅ Collector done")
except Exception as e:
    print("❌ Collector error:", e)

# =========================
# ANALYZER
# =========================
try:
    print("🧠 Running analyzer...")
    analyzer_main()
    print("✅ Analyzer done")
except Exception as e:
    print("❌ Analyzer error:", e)

end = time.time()

print(f"🏁 CYCLE FINISHED in {round(end - start, 2)}s")
