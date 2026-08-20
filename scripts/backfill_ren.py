import time
from datetime import date, timedelta

from app import create_app
from app.services.ingestion import ingest_production_day

DAYS_BACK = 180


def run():
    app = create_app()

    # App context needed to reach the database outside an HTTP request
    with app.app_context():
        # Ends at D-7 to match the weather archive lag, so both
        # backfills cover exactly the same range.
        end = date.today() - timedelta(days=7)
        start = end - timedelta(days=DAYS_BACK)

        print(f"Backfill from {start} to {end}")

        current = start
        while current <= end:
            try:
                # Same function the scheduled job uses
                count = ingest_production_day(current)
                print(f"{current}: {count} records")
            except Exception as error:
                # One failed day must not stop the other 179
                print(f"{current}: FAILED -> {error}")

            # Small pause out of courtesy to the REN server
            time.sleep(0.5)
            current += timedelta(days=1)

    print("Backfill complete.")


if __name__ == "__main__":
    run()