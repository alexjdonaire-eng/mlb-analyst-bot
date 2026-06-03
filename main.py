import collector
import analyzer

def main():
    print("🏦 SHARP MONEY V4 INSTITUTIONAL START")

    games = collector.run()
    report = analyzer.run(games)

    print("🏁 CYCLE COMPLETE")

if __name__ == "__main__":
    main()
