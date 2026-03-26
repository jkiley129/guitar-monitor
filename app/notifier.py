import logging

import telegram

from app.database import db, get_setting
from app.models import Match

logger = logging.getLogger(__name__)


def _get_bot_and_chat():
    token = get_setting("telegram_token")
    chat_id = get_setting("telegram_chat_id")
    if not token or not chat_id:
        return None, None
    return telegram.Bot(token=token), chat_id


def format_message(match):
    price_str = f"${match.price:,}" if match.price else "No price listed"
    city_label = match.city.replace("_", " ").title()
    return (
        f"<b>{match.title}</b>\n"
        f"{price_str} — {city_label}\n"
        f"<a href=\"{match.url}\">View on Craigslist</a>\n"
        f"<i>Search: {match.search.name}</i>"
    )


def send_pending_notifications():
    bot, chat_id = _get_bot_and_chat()
    if not bot:
        logger.debug("Telegram not configured, skipping notifications")
        return 0

    unsent = Match.query.filter_by(notified=0).all()
    sent = 0
    for match in unsent:
        text = format_message(match)
        try:
            if match.image_url:
                bot.send_photo(chat_id=chat_id, photo=match.image_url, caption=text, parse_mode="HTML")
            else:
                bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            match.notified = 1
            db.session.commit()
            sent += 1
        except Exception as e:
            logger.warning(f"Telegram send failed for match {match.id}: {e}")
    return sent


def send_test_message():
    bot, chat_id = _get_bot_and_chat()
    if not bot:
        return False, "Telegram not configured. Set token and chat ID in Settings."
    try:
        bot.send_message(chat_id=chat_id, text="Guitar Monitor is connected and working!", parse_mode="HTML")
        return True, "Test message sent successfully."
    except Exception as e:
        return False, f"Failed to send: {e}"
