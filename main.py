import collector
import analyzer

def main():
    print("🚀 SHARP MONEY BOT V3 START")

    games = collector.run()
    report = analyzer.run(games)

    print("🏁 CYCLE FINISHED")

if __name__ == "__main__":
    main()
