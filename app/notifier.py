import logging
import requests

from app.database import db, get_setting
from app.models import Match
from app.poller import CITY_LABELS

logger = logging.getLogger(__name__)

NTFY_BASE = "https://ntfy.sh"


def _ntfy_topic():
    return get_setting("ntfy_topic", "").strip()


def send_pending_notifications():
    topic = _ntfy_topic()
    if not topic:
        logger.debug("ntfy topic not configured, skipping notifications")
        return 0

    unsent = Match.query.filter_by(notified=0).all()
    sent = 0
    for match in unsent:
        try:
            _send_ntfy(topic, match)
            match.notified = 1
            db.session.commit()
            sent += 1
        except Exception as e:
            logger.warning(f"ntfy send failed for match {match.id}: {e}")
    return sent


def _send_ntfy(topic, match):
    price_str = f"${match.price:,}" if match.price else "No price listed"
    city_label = CITY_LABELS.get(match.city, match.city)

    safe_title = match.title.encode("latin-1", errors="replace").decode("latin-1")
    safe_url = match.url.encode("latin-1", errors="replace").decode("latin-1")
    headers = {
        "Title": f"{safe_title} - {price_str}",
        "Tags": "guitar,money_with_wings",
        "Click": safe_url,
        "Actions": f"view, View on Craigslist, {safe_url}",
        "Priority": "default",
    }

    body = f"{city_label}  |  Search: {match.search.name}"

    resp = requests.post(f"{NTFY_BASE}/{topic}", data=body.encode("utf-8"), headers=headers, timeout=10)
    resp.raise_for_status()


def send_test_notification():
    topic = _ntfy_topic()
    if not topic:
        return False, "No ntfy topic configured. Enter a topic name and save first."
    try:
        resp = requests.post(
            f"{NTFY_BASE}/{topic}",
            data=b"Guitar Monitor is connected! You'll get alerts here when new listings are found.",
            headers={
                "Title": "Guitar Monitor - Test",
                "Tags": "guitar,white_check_mark",
                "Priority": "default",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True, f"Sent! Check your ntfy app — topic: {topic}"
    except requests.HTTPError as e:
        return False, f"ntfy rejected the request ({e.response.status_code}): {e.response.text}"
    except Exception as e:
        return False, f"Network error: {e}"
