import re
import time
import json
import logging

import requests

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Matches listing URLs like /abc/msa/d/title-here/1234567890.html
LISTING_URL_RE = re.compile(r'https://[a-z]+\.craigslist\.org/[^"]+/d/[^"]+/(\d+)\.html')


def build_search_url(city, keywords, min_price=None, max_price=None, posted_today=True):
    params = f"query={keywords.replace(' ', '+')}&sort=date"
    if posted_today:
        params += "&postedToday=1"
    if min_price:
        params += f"&min_price={min_price}"
    if max_price:
        params += f"&max_price={max_price}"
    return f"https://{city}.craigslist.org/search/msa?{params}"


def fetch_listings(city, keywords, min_price=None, max_price=None, posted_today=True):
    url = build_search_url(city, keywords, min_price, max_price, posted_today)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"CL {city} returned {resp.status_code}")
            return []
        return _parse_listings(resp.text, city)
    except Exception as e:
        logger.warning(f"Error fetching {city}: {e}")
        return []


def _parse_listings(html, city):
    # Extract listing URLs from HTML (with the numeric ID)
    listing_urls = LISTING_URL_RE.findall(html)
    url_map = {}  # id -> full url
    for match in LISTING_URL_RE.finditer(html):
        url_map[match.group(1)] = match.group(0)

    # Extract structured data from the embedded JSON schema script tag
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    schema_items = []
    for script in scripts:
        if '"itemListElement"' in script:
            try:
                data = json.loads(script)
                items = data.get("itemListElement", [])
                if items:  # keep going until we find the non-empty one
                    schema_items = items
                    break
            except Exception:
                pass

    listings = []
    for entry in schema_items:
        item = entry.get("item", {})
        position = int(entry.get("position", 0))

        title = item.get("name", "").strip()
        if not title:
            continue

        # Get price
        offers = item.get("offers", {})
        price_str = offers.get("price")
        price = int(float(price_str)) if price_str else None

        # Get image
        images = item.get("image", [])
        image_url = images[0] if images else None

        # Get location
        place = offers.get("availableAtOrFrom", {})
        address = place.get("address", {})
        locality = address.get("addressLocality", "")

        # Get listing URL by matching position to URLs in HTML
        # URLs appear in the same order as schema items
        all_matches = list(LISTING_URL_RE.finditer(html))
        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for m in all_matches:
            lid = m.group(1)
            if lid not in seen:
                seen.add(lid)
                unique_urls.append((lid, m.group(0)))

        if position < len(unique_urls):
            listing_id, url = unique_urls[position]
        else:
            continue

        listings.append({
            "listing_id": listing_id,
            "title": title,
            "price": price,
            "city": city,
            "locality": locality,
            "url": url,
            "image_url": image_url,
        })

    return listings


def poll_all_searches():
    searches = Search.query.filter_by(active=1).all()
    results = {}
    for search in searches:
        count = _poll_search(search)
        results[search.name] = count
    total = sum(results.values())
    logger.info(f"Poll complete — {total} new matches found")
    return results


def _poll_search(search):
    cities = search.cities if search.cities else CITIES
    new_count = 0
    for city in cities:
        try:
            listings = fetch_listings(city, search.keywords, search.min_price, search.max_price, bool(search.posted_today))
            for l in listings:
                existing = Match.query.filter_by(
                    listing_id=l["listing_id"], search_id=search.id
                ).first()
                if not existing:
                    match = Match(
                        search_id=search.id,
                        listing_id=l["listing_id"],
                        title=l["title"],
                        price=l["price"],
                        city=l["city"],
                        url=l["url"],
                        image_url=l["image_url"],
                        description=l.get("locality"),
                    )
                    db.session.add(match)
                    new_count += 1
        except Exception as e:
            logger.warning(f"Error polling {city} for '{search.name}': {e}")
        time.sleep(1)

    db.session.commit()
    return new_count
