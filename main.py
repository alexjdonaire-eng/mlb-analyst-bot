import collector
import analyzer
import time

def main():

    print("🏦 SHARP MONEY V4 INSTITUTIONAL START")

    games = collector.run()

    report = analyzer.run(games)

    print("🏁 CYCLE COMPLETE")

    time.sleep(300)

if __name__ == "__main__":
    main()
