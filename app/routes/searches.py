from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.database import db
from app.models import Search
from app.poller import CITIES, CITY_LABELS

searches_bp = Blueprint("searches", __name__, url_prefix="/searches")


@searches_bp.route("/")
def index():
    searches = Search.query.order_by(Search.created_at.desc()).all()
    return render_template("searches/index.html", searches=searches)


@searches_bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        return _save_search(None)
    return render_template("searches/form.html", search=None, cities=CITIES, city_labels=CITY_LABELS, selected_cities=CITIES)


@searches_bp.route("/<int:search_id>/edit", methods=["GET", "POST"])
def edit(search_id):
    search = Search.query.get_or_404(search_id)
    if request.method == "POST":
        return _save_search(search)
    return render_template(
        "searches/form.html",
        search=search,
        cities=CITIES,
        city_labels=CITY_LABELS,
        selected_cities=search.cities,
    )


@searches_bp.route("/<int:search_id>/delete", methods=["POST"])
def delete(search_id):
    search = Search.query.get_or_404(search_id)
    db.session.delete(search)
    db.session.commit()
    flash(f'Search "{search.name}" deleted.', "success")
    return redirect(url_for("searches.index"))


@searches_bp.route("/<int:search_id>/toggle", methods=["POST"])
def toggle(search_id):
    search = Search.query.get_or_404(search_id)
    search.active = 0 if search.active else 1
    db.session.commit()
    return redirect(url_for("searches.index"))


def _save_search(search):
    name = request.form.get("name", "").strip()
    keywords = request.form.get("keywords", "").strip()
    min_price = request.form.get("min_price") or None
    max_price = request.form.get("max_price") or None
    posted_today = 1 if request.form.get("posted_today") else 0
    selected_cities = request.form.getlist("cities")

    if not name or not keywords:
        flash("Name and keywords are required.", "danger")
        return redirect(request.url)

    if not selected_cities:
        selected_cities = CITIES

    if search is None:
        search = Search(name=name, keywords=keywords)
        db.session.add(search)
    else:
        search.name = name
        search.keywords = keywords

    search.min_price = int(min_price) if min_price else None
    search.max_price = int(max_price) if max_price else None
    search.posted_today = posted_today
    search.cities = selected_cities
    db.session.commit()
    flash(f'Search "{search.name}" saved.', "success")
    return redirect(url_for("searches.index"))
