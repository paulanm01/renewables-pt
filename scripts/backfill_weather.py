import time
from datetime import date, timedelta

from app import create_app
from app.clients.open_meteo_client import fetch_weather, CITIES
from app.extensions import db
from app.models.weather import WeatherRecord

DAYS_BACK = 180


def run():
    app = create_app()

    with app.app_context():
        # Same range as the REN backfill, so the correlation has
        # production and weather for the same hours.
        end = date.today() - timedelta(days=7)
        start = end - timedelta(days=DAYS_BACK)

        print(f"Weather backfill from {start} to {end}")

        # Loops over cities, not days: unlike REN, one request covers
        # the whole range. Five cities cost five requests in total,
        # which is why this does not reuse ingest_weather_day().
        for city, (latitude, longitude) in CITIES.items():
            try:
                rows = fetch_weather(city, latitude, longitude, start, end)
            except Exception as error:
                # One failed city must not stop the other four
                print(f"{city}: FAILED -> {error}")
                continue

            # Deletes the whole city because the whole range is being
            # rewritten. The daily job deletes by city AND day instead,
            # since it only touches one day.
            WeatherRecord.query.filter(
                WeatherRecord.city == city
            ).delete(synchronize_session=False)

            for item in rows:
                db.session.add(WeatherRecord(**item))

            db.session.commit()

            print(f"{city}: {len(rows)} records")

            time.sleep(0.5)

    print("Weather backfill complete.")


if __name__ == "__main__":
    run()