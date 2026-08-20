from datetime import datetime

import requests

from app.constants import SERIES_CATEGORY

BASE_URL = ("https://servicebus.ren.pt/datahubapi/electricity/"
            "ElectricityProductionBreakdownDaily")


def parse_production(payload, target_date):
    """Turn the API response into rows ready to be stored.

    Does not touch the network: it takes the JSON already loaded.
    That is what makes it testable with made-up data, offline.
    """
    # The REN response is shaped for a charting library, not for data
    # consumption. Times live in xAxis.categories: ["00:00", "00:15", ...]
    # and values live in a separate array per series.
    times = payload["xAxis"]["categories"]

    rows = []

    # For each series, match every value with the time at the SAME
    # POSITION. Nothing else links them.
    for series in payload["series"]:
        name = series["name"]
        category = SERIES_CATEGORY.get(name)

        # Unknown series: skip instead of crashing, but WARN.
        # Staying silent here would mean losing data without noticing.
        # Using .get() rather than [name] is what allows this.
        if category is None:
            print(f"WARNING: unclassified series -> {name!r}")
            continue

        # zip pairs the two parallel lists position by position
        for time_label, value in zip(times, series["data"]):
            # Missing values: skip rather than store a null
            if value is None:
                continue

            # The API only gives the time of day, so the date comes
            # from the parameter: "07:15" -> datetime(2026, 8, 1, 7, 15)
            hour, minute = time_label.split(":")
            recorded_at = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                int(hour),
                int(minute),
            )

            rows.append({
                "recorded_at": recorded_at,
                "source": name,
                "category": category,
                "value_mw": value,
            })

    return rows


def fetch_production(target_date):
    """Fetch one day of production from the REN API.

    target_date: a date object
    Returns: list of dicts with recorded_at, source, category, value_mw
    """
    # The timeout stops this hanging forever if REN does not respond.
    response = requests.get(
        BASE_URL,
        params={"culture": "pt-PT", "date": target_date.isoformat()},
        timeout=30,
    )
    # Raise on 4xx/5xx. Without this, an error page would reach .json()
    # and fail with a confusing message about invalid characters.
    response.raise_for_status()

    return parse_production(response.json(), target_date)