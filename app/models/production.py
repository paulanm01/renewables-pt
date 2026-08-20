from app.extensions import db


class ProductionRecord(db.Model):
    """One reading of one source at one point in time.

    Long format: one row per (timestamp, source) instead of one column
    per source. A new source from REN becomes extra rows, not a schema
    change.
    """

    __tablename__ = "production_records"

    id = db.Column(db.Integer, primary_key=True)

    # The moment the value refers to (15-minute intervals)
    recorded_at = db.Column(db.DateTime, nullable=False, index=True)

    # Series name exactly as REN returns it: "Solar", "Eólica", ...
    source = db.Column(db.String(50), nullable=False, index=True)

    # renewable / non_renewable / not_production / storage
    # Stored here so we can filter by category in SQL, instead of
    # reclassifying in Python every time.
    category = db.Column(db.String(20), nullable=False, index=True)

    value_mw = db.Column(db.Float, nullable=False)

    __table_args__ = (
        # Stops duplicates if the backfill runs twice.
        # Without this, every total would silently double.
        db.UniqueConstraint("recorded_at", "source",
                            name="uq_production_time_source"),
    )

    def __repr__(self):
        return f"<ProductionRecord {self.recorded_at} {self.source}={self.value_mw}>"