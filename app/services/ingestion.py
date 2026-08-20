from datetime import datetime, timedelta

from app.extensions import db
from app.clients.ren_client import fetch_production
from app.clients.open_meteo_client import fetch_weather, CITIES
from app.models.production import ProductionRecord
from app.models.weather import WeatherRecord


def ingest_production_day(target_date):
    """Fetch and store one day of production. Idempotent.

    Shared by the backfill script and the scheduled job, so there is
    one implementation of the write logic rather than two that could
    drift apart.

    Returns the number of records inserted.
    """
    rows = fetch_production(target_date)

    # Delete the day before reinserting, so the function can run any
    # number of times without duplicating or hitting the unique
    # constraint. Delete and insert share one transaction, so the day
    # is never left deleted but not rewritten.
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    ProductionRecord.query.filter(
        ProductionRecord.recorded_at >= day_start,
        ProductionRecord.recorded_at < day_end,
    ).delete(synchronize_session=False)

    for item in rows:
        db.session.add(ProductionRecord(**item))

    db.session.commit()
    return len(rows)


def ingest_weather_day(target_date):
    """Fetch and store one day of weather for all five cities.

    Returns the total number of records inserted.
    """
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    total = 0

    for city, (latitude, longitude) in CITIES.items():
        rows = fetch_weather(city, latitude, longitude,
                             target_date, target_date)

        # Filtered by city AND day. The backfill deletes a whole city
        # because it rewrites the full range; here we touch one day, so
        # deleting the whole city would wipe six months to write one.
        WeatherRecord.query.filter(
            WeatherRecord.city == city,
            WeatherRecord.recorded_at >= day_start,
            WeatherRecord.recorded_at < day_end,
        ).delete(synchronize_session=False)

        for item in rows:
            db.session.add(WeatherRecord(**item))

        total += len(rows)

    db.session.commit()
    return total