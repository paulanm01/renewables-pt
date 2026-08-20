from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.ingestion import ingest_production_day, ingest_weather_day

# Weather archive lag: ERA5 data only becomes available 5 to 7 days
# later. Aligning collection with the slower source means both always
# arrive complete, through one code path instead of special cases.
LAG_DAYS = 7


def daily_job(app):
    """Ingest day D-7 from both sources."""
    with app.app_context():
        target = date.today() - timedelta(days=LAG_DAYS)

        # Two separate try blocks on purpose: if REN fails, weather
        # should still be collected. One block around both would let
        # a single failure cancel the other.
        try:
            count = ingest_production_day(target)
            print(f"[scheduler] {target}: {count} production records")
        except Exception as error:
            print(f"[scheduler] {target}: production FAILED -> {error}")

        try:
            count = ingest_weather_day(target)
            print(f"[scheduler] {target}: {count} weather records")
        except Exception as error:
            print(f"[scheduler] {target}: weather FAILED -> {error}")


def start_scheduler(app):
    """Start the background scheduler.

    APScheduler runs inside the Flask process, which is why this
    project is not deployed to a free cloud tier - the app would
    sleep on inactivity and the scheduler would sleep with it.
    """
    scheduler = BackgroundScheduler(timezone="Europe/Lisbon")

    # Every day at 06:00, Portuguese time
    scheduler.add_job(daily_job, "cron", hour=6, args=[app], id="daily_ingest")

    scheduler.start()
    return scheduler