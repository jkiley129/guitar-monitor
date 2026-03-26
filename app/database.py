from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    # Enable WAL mode to prevent write contention between web thread and scheduler
    @event.listens_for(db.engine, "connect")
    def set_wal_mode(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    with app.app_context():
        db.create_all()
        _seed_settings()


def _seed_settings():
    from app.models import Setting
    defaults = [
        ("telegram_token", ""),
        ("telegram_chat_id", ""),
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
