from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy's metadata knows about all tables
        import app.models  # noqa: F401

        # Enable WAL mode — must be inside app context to access db.engine
        @event.listens_for(db.engine, "connect")
        def set_wal_mode(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")

        db.create_all()
        _migrate(db.engine)
        _seed_settings()


def _migrate(engine):
    """Add columns that were introduced after initial release."""
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(db.text("PRAGMA table_info(searches)"))]
        if "posted_today" not in cols:
            conn.execute(db.text("ALTER TABLE searches ADD COLUMN posted_today INTEGER NOT NULL DEFAULT 1"))
            conn.commit()


def _seed_settings():
    from app.models import Setting
    defaults = [
        ("ntfy_topic", ""),
        ("poll_interval_minutes", "20"),
    ]
    for key, value in defaults:
        if not Setting.query.get(key):
            db.session.add(Setting(key=key, value=value))
    db.session.commit()


def get_setting(key, default=None):
    import os
    from app.models import Setting
    row = Setting.query.get(key)
    if row and row.value:
        return row.value
    return os.environ.get(key.upper(), default)


def set_setting(key, value):
    from app.models import Setting
    row = Setting.query.get(key)
    if row:
        row.value = value
    else:
        db.session.add(Setting(key=key, value=value))
    db.session.commit()
