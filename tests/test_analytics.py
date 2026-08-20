"""Tests for the data transformation layer.

No internet or database needed: these test pure functions with
made-up data. That is why the parsing was separated from the HTTP
call in the REN client.
"""

from datetime import date

from app.clients.ren_client import parse_production
from app.constants import SERIES_CATEGORY, RENEWABLE, NOT_PRODUCTION


def test_series_classification():
    """Every REN series must map to the right category."""
    assert SERIES_CATEGORY["Solar"] == RENEWABLE
    assert SERIES_CATEGORY["Eólica"] == RENEWABLE

    # "Consumo" arrives in the production endpoint but is NOT
    # production. Adding it to totals would inflate every figure.
    assert SERIES_CATEGORY["Consumo"] == NOT_PRODUCTION

    # Unknown series return None rather than raising, so a new series
    # from REN cannot break the backfill.
    assert SERIES_CATEGORY.get("Fusão Nuclear") is None


def test_parse_production_aligns_times_with_values():
    """The value at position N must end up with the time at position N."""
    payload = {
        "xAxis": {"categories": ["00:00", "00:15", "00:30"]},
        "series": [
            {"name": "Solar", "data": [0.0, 5.5, 12.3]},
            {"name": "Eólica", "data": [800.1, 811.2, 790.0]},
        ],
    }

    rows = parse_production(payload, date(2026, 8, 1))

    # 3 times x 2 series
    assert len(rows) == 6

    solar = [r for r in rows if r["source"] == "Solar"]

    # Solar's second value (5.5) must sit at 00:15
    assert solar[1]["value_mw"] == 5.5
    assert solar[1]["recorded_at"].hour == 0
    assert solar[1]["recorded_at"].minute == 15

    # The requested date must appear in the result: the API only
    # returns the time of day, the date comes from the parameter.
    assert solar[1]["recorded_at"].date() == date(2026, 8, 1)

    # The category is assigned from the series name
    assert solar[0]["category"] == RENEWABLE


def test_parse_production_skips_null_values():
    """Missing values are skipped, not stored as nulls."""
    payload = {
        "xAxis": {"categories": ["00:00", "00:15"]},
        "series": [{"name": "Solar", "data": [10.0, None]}],
    }

    rows = parse_production(payload, date(2026, 8, 1))

    assert len(rows) == 1
    assert rows[0]["value_mw"] == 10.0


def test_parse_production_ignores_unknown_series():
    """A series REN might add must not break the backfill."""
    payload = {
        "xAxis": {"categories": ["00:00"]},
        "series": [
            {"name": "Solar", "data": [10.0]},
            {"name": "Série Inventada", "data": [99.0]},
        ],
    }

    rows = parse_production(payload, date(2026, 8, 1))

    # Only Solar goes through; the unknown series is skipped with a warning
    assert len(rows) == 1
    assert rows[0]["source"] == "Solar"