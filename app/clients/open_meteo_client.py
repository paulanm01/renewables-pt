from datetime import datetime

import requests

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Five cities chosen to cover the country north to south.
# REN production is national, weather is local: the average of these
# five works as a PROXY for conditions across Portugal.
CITIES = {
    "Lisboa": (38.72, -9.14),
    "Porto": (41.15, -8.61),
    "Faro": (37.02, -7.93),
    "Évora": (38.57, -7.91),
    "Bragança": (41.81, -6.76),
}


def fetch_weather(city, latitude, longitude, start_date, end_date):
    """Return hourly rows for one city over a date range.

    Unlike the REN API, one request covers the whole range, so five
    cities cost five requests in total rather than five per day.

    Returns: list of dicts with city, recorded_at, temperature_c,
             shortwave_radiation, wind_speed_kmh
    """
    response = requests.get(
        BASE_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": "temperature_2m,shortwave_radiation,wind_speed_10m",
            # WITHOUT this the times come back in UTC and drift out of
            # line with REN, which publishes in Portuguese local time.
            "timezone": "Europe/Lisbon",
        },
        timeout=60,
    )
    response.raise_for_status()
    hourly = response.json()["hourly"]

    rows = []

    # Same pattern as REN: parallel lists matched by position.
    # The difference is there are four lists here instead of two.
    for moment, temp, radiation, wind in zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["shortwave_radiation"],
        hourly["wind_speed_10m"],
    ):
        # Here the full timestamp comes in the response, in ISO format,
        # so there is no need to build it by hand.
        recorded_at = datetime.fromisoformat(moment)

        rows.append({
            "city": city,
            "recorded_at": recorded_at,
            "temperature_c": temp,
            "shortwave_radiation": radiation,
            # No None check here on purpose: these columns accept nulls,
            # so a missing reading should not cost us the whole hour.
            "wind_speed_kmh": wind,
        })

    return rows