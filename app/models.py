import json
from app.database import db


class Search(db.Model):
    __tablename__ = "searches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=False)
    min_price = db.Column(db.Integer, nullable=True)
    max_price = db.Column(db.Integer, nullable=True)
    _cities = db.Column("cities", db.Text, nullable=False, default="[]")
    posted_today = db.Column(db.Integer, nullable=False, default=1)  # 1 = today only
    active = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.Text, nullable=False, server_default=db.func.datetime("now"))

    matches = db.relationship("Match", backref="search", cascade="all, delete-orphan", lazy=True)

    @property
    def cities(self):
        return json.loads(self._cities)

    @cities.setter
    def cities(self, value):
        self._cities = json.dumps(value)

    @property
    def unseen_count(self):
        return Match.query.filter_by(search_id=self.id, seen=0).count()


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    listing_id = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=True)
    city = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    posted_at = db.Column(db.Text, nullable=True)
    seen = db.Column(db.Integer, nullable=False, default=0)
    notified = db.Column(db.Integer, nullable=False, default=0)
    found_at = db.Column(db.Text, nullable=False, server_default=db.func.datetime("now"))

    __table_args__ = (
        db.UniqueConstraint("listing_id", "search_id", name="uq_listing_search"),
    )

    @property
    def price_display(self):
        return f"${self.price:,}" if self.price else "—"


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text, nullable=True)
