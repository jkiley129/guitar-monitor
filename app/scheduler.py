import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import get_setting

logger = logging.getLogger(__name__)

_scheduler = None


def run_poll_cycle(app):
    with app.app_context():
        from app.poller import poll_all_searches
        from app.notifier import send_pending_notifications
        try:
            results = poll_all_searches()
            sent = send_pending_notifications()
            total = sum(results.values())
            logger.info(f"Cycle done — {total} new matches, {sent} notifications sent")
            return results, sent
        except Exception as e:
            logger.error(f"Poll cycle error: {e}")
            return {}, 0


def start_scheduler(app):
    global _scheduler
    with app.app_context():
        interval = int(get_setting("poll_interval_minutes") or 20)
    import pytz
    _scheduler = BackgroundScheduler(daemon=True, timezone=pytz.utc)
    _scheduler.add_job(
        func=lambda: run_poll_cycle(app),
        trigger="interval",
        minutes=interval,
        id="poll_craigslist",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"Scheduler started — polling every {interval} minutes")


def reschedule(minutes):
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.reschedule_job("poll_craigslist", trigger="interval", minutes=int(minutes))
        logger.info(f"Scheduler rescheduled to every {minutes} minutes")


def trigger_now(app):
    return run_poll_cycle(app)
