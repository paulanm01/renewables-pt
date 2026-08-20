import pandas as pd

from app.constants import RENEWABLE
from app.extensions import db
from app.models.production import ProductionRecord
from app.models.weather import WeatherRecord


def _production_df(start=None, end=None, source=None):
    """Return a filtered DataFrame of production records.

    The leading underscore is a Python convention: it marks this as
    internal to the module, not meant to be called from outside.
    """
    query = db.session.query(ProductionRecord)

    # Guard clauses: only add a filter if the parameter was given.
    # This lets the function be called with no filters at all.
    if start:
        query = query.filter(ProductionRecord.recorded_at >= start)
    if end:
        query = query.filter(ProductionRecord.recorded_at <= end)
    if source:
        query = query.filter(ProductionRecord.source == source)

    # SQL guarantees no order unless asked. resample() below needs a
    # sorted index, so the ordering is not optional.
    query = query.order_by(ProductionRecord.recorded_at)

    # read_sql runs the query and builds the DataFrame directly,
    # skipping the ORM. Instantiating 260k Python objects just to
    # aggregate them would waste memory and time.
    return pd.read_sql(query.statement, db.engine)


def production_timeline(start=None, end=None, source=None):
    """Daily average production per source.

    Returns: list of dicts with day, source, avg_mw
    """
    df = _production_df(start, end, source)

    if df.empty:
        return []

    # Text, not a date object: jsonify cannot serialise date objects,
    # and ISO format sorts chronologically as a string.
    df["day"] = df["recorded_at"].dt.strftime("%Y-%m-%d")

    # Mean, not sum. These are MW readings - instantaneous power.
    # Adding 96 power readings together does not give energy.
    daily = df.groupby(["day", "source"])["value_mw"].mean().round(1)

    return (
        daily.reset_index()
        .rename(columns={"value_mw": "avg_mw"})
        .to_dict("records")
    )


def weather_production_correlation(source="Solar", start=None, end=None):
    """Correlation between weather conditions and one source's output."""
    prod = _production_df(start, end, source)
    weather = pd.read_sql(
        db.session.query(WeatherRecord).statement, db.engine
    )

    if prod.empty or weather.empty:
        return {"error": "No data."}

    # 1. Production is every 15 minutes, weather is hourly. Resample
    #    production down to match. resample() needs the datetime as
    #    the index, hence set_index first.
    prod = prod.set_index("recorded_at")
    prod_hourly = prod["value_mw"].resample("h").mean()

    # 2. Average the 5 cities for each hour. This is the national
    #    PROXY: REN production covers the whole country, but weather
    #    is measured at points.
    weather_national = weather.groupby("recorded_at")[
        ["temperature_c", "shortwave_radiation", "wind_speed_kmh"]
    ].mean()

    # 3. how="inner" keeps only hours present in BOTH tables, so no
    #    half-empty rows end up in the correlation.
    merged = prod_hourly.to_frame().join(weather_national, how="inner")

    # corr() returns a full matrix; we only want the production column
    correlations = merged.corr()["value_mw"]

    # Drop production's correlation with itself, which is always 1.0
    correlations = correlations.drop("value_mw")

    # Round at the output, never in the intermediate steps
    return {
        "source": source,
        "hours_compared": len(merged),
        "correlations": correlations.round(3).to_dict(),
    }


def insights(start=None, end=None):
    """Notable facts for the period: records and volatility."""
    df = _production_df(start, end)

    if df.empty:
        return {"error": "No data."}

    # Real production only. Consumption, cross-border trade and
    # storage are excluded, or demand would be counted as generation.
    production = df[df["category"].isin(["renewable", "non_renewable"])].copy()
    production["day"] = production["recorded_at"].dt.strftime("%Y-%m-%d")

    by_day = production.groupby(["day", "category"])["value_mw"].mean()

    # unstack turns the categories into columns:
    # (day, category) -> value   becomes   day -> renewable, non_renewable
    # This is what puts both values on the same row so the share
    # can be calculated.
    daily = by_day.unstack(fill_value=0)
    daily["total"] = daily.sum(axis=1)
    daily["renewable_pct"] = (daily[RENEWABLE] / daily["total"] * 100).round(1)

    # idxmax gives the day, max gives the value
    best_day = daily["renewable_pct"].idxmax()
    best_value = daily["renewable_pct"].max()

    worst_day = daily["renewable_pct"].idxmin()
    worst_value = daily["renewable_pct"].min()

    # Relative volatility: standard deviation over mean. The plain
    # standard deviation would always favour the source with the
    # biggest numbers, regardless of how steady it is.
    renewables = df[df["category"] == RENEWABLE]
    stats = renewables.groupby("source")["value_mw"].agg(["mean", "std"])
    volatility = stats["std"] / stats["mean"]

    # float() because jsonify cannot serialise NumPy types
    return {
        "period_days": len(daily),
        "avg_renewable_pct": round(daily["renewable_pct"].mean(), 1),
        "best_day": {
            "day": best_day,
            "renewable_pct": float(best_value),
        },
        "worst_day": {
            "day": worst_day,
            "renewable_pct": float(worst_value),
        },
        "most_volatile_source": volatility.idxmax(),
    }