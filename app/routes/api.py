from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services import analytics

bp = Blueprint("api", __name__, url_prefix="/api")


def _parse_date(value):
    """Validate a date string in YYYY-MM-DD format.

    Returns None if the parameter was not given, which is valid and
    means "no filter". Raises ValueError if it was given but malformed.
    """
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


@bp.route("/production/timeline")
def production_timeline():
    """Daily average production per source over a date range."""
    # Parameters are validated here, before they reach the database.
    # A bad parameter is the client's fault, so it returns 400 - not
    # the 500 that an unhandled database error would produce.
    try:
        start = _parse_date(request.args.get("start"))
        end = _parse_date(request.args.get("end"))
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    source = request.args.get("source")

    # Keyword arguments: the analytics functions take three parameters
    # and swapping two of the same type would fail silently.
    return jsonify(analytics.production_timeline(
        start=start, end=end, source=source
    ))


@bp.route("/correlation/weather-production")
def weather_correlation():
    """Correlation between weather and one source's output."""
    try:
        start = _parse_date(request.args.get("start"))
        end = _parse_date(request.args.get("end"))
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Solar by default: it has the clearest correlation
    source = request.args.get("source", "Solar")

    return jsonify(analytics.weather_production_correlation(
        source=source, start=start, end=end
    ))


@bp.route("/insights")
def get_insights():
    """Notable facts: renewable share records and volatility."""
    try:
        start = _parse_date(request.args.get("start"))
        end = _parse_date(request.args.get("end"))
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    return jsonify(analytics.insights(start=start, end=end))