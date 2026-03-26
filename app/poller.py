import re
import time
import logging

import feedparser

from app.database import db
from app.models import Search, Match

logger = logging.getLogger(__name__)

CITIES = [
    "sfbay", "losangeles", "newyork", "chicago", "seattle", "portland",
    "austin", "denver", "nashville", "atlanta", "miami", "boston",
    "dallas", "houston", "phoenix", "philadelphia", "minneapolis", "washingtondc",
]

CITY_LABELS = {
    "sfbay": "San Francisco Bay",
    "losangeles": "Los Angeles",
    "newyork": "New York",
    "chicago": "Chicago",
    "seattle": "Seattle",
    "portland": "Portland",
    "austin": "Austin",
    "denver": "Denver",
    "nashville": "Nashville",
    "atlanta": "Atlanta",
    "miami": "Miami",
    "boston": "Boston",
    "dallas": "Dallas",
    "houston": "Houston",
    "phoenix": "Phoenix",
    "philadelphia": "Philadelphia",
    "minneapolis": "Minneapolis",
    "washingtondc": "Washington DC",
}

PRICE_RE = re.compile(r"\$(\d+(?:,\d{3})*)")


def build_rss_url(city, keywords, min_price=None, max_price=None):
    params = f"format=rss&query={keywords.replace(' ', '+')}"
    if min_price:
        params += f"&min_price={min_price}"
    if max_price:
        params += f"&max_price={max_price}"
    return f"https://{city}.craigslist.org/search/msa?{params}"


def parse_price(title):
    match = PRICE_RE.search(title or "")
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def poll_all_searches():
    searches = Search.query.filter_by(active=1).all()
    new_count = 0
    for search in searches:
        new_count += _poll_search(search)
    logger.info(f"Poll complete — {new_count} new matches found")
    return new_count


def _poll_search(search):
    cities = search.cities if search.cities else CITIES
    new_count = 0
    for city in cities:
        url = build_rss_url(city, search.keywords, search.min_price, search.max_price)
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                listing_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                if not listing_id:
                    continue
                title = getattr(entry, "title", "")
                price = parse_price(title)
                link = getattr(entry, "link", "")
                summary = getattr(entry, "summary", "")
                published = getattr(entry, "published", None)
                image_url = None
                enclosures = getattr(entry, "enclosures", [])
                if enclosures:
                    image_url = enclosures[0].get("url")

                existing = Match.query.filter_by(
                    listing_id=listing_id, search_id=search.id
                ).first()
                if not existing:
                    match = Match(
                        search_id=search.id,
                        listing_id=listing_id,
                        title=title,
                        price=price,
                        city=city,
                        url=link,
                        image_url=image_url,
                        description=summary[:500] if summary else None,
                        posted_at=published,
                    )
                    db.session.add(match)
                    new_count += 1
        except Exception as e:
            logger.warning(f"Error polling {city} for search '{search.name}': {e}")
        time.sleep(0.5)

    db.session.commit()
    return new_count
