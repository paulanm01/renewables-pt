from app.extensions import db


class WeatherRecord(db.Model):
    """Hourly weather reading for one of the five proxy cities."""

    __tablename__ = "weather_records"

    id = db.Column(db.Integer, primary_key=True)

    # One of the 5 cities used as a proxy for national weather
    city = db.Column(db.String(50), nullable=False, index=True)

    # The moment of the reading (hourly)
    recorded_at = db.Column(db.DateTime, nullable=False, index=True)

    # Nullable on purpose: the weather archive can have gaps, and one
    # missing reading should not break the whole insert.
    # Compare with value_mw above, which is required - a production
    # row with no value would be meaningless.
    temperature_c = db.Column(db.Float)
    shortwave_radiation = db.Column(db.Float)

    # Unit in the column name: the API returns km/h, and forgetting
    # that would make every figure wrong by a factor of 3.6.
    wind_speed_kmh = db.Column(db.Float)

    __table_args__ = (
        # Each city has ONE reading per hour. The pair is (who, when):
        # filtering on time alone would reject four of the five cities.
        db.UniqueConstraint("city", "recorded_at",
                            name="uq_weather_city_time"),
    )

    def __repr__(self):
        return f"<WeatherRecord {self.recorded_at} {self.city}={self.temperature_c}>"