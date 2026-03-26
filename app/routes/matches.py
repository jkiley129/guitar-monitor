from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from app.database import db
from app.models import Match, Search

matches_bp = Blueprint("matches", __name__)


@matches_bp.context_processor
def inject_unseen_total():
    try:
        unseen_total = Match.query.filter_by(seen=0).count()
    except Exception:
        unseen_total = 0
    return {"unseen_total": unseen_total}


@matches_bp.route("/")
def index():
    search_id = request.args.get("search_id", type=int)
    unseen_only = request.args.get("unseen_only", type=int, default=0)
    page = request.args.get("page", 1, type=int)

    query = Match.query
    if search_id:
        query = query.filter_by(search_id=search_id)
    if unseen_only:
        query = query.filter_by(seen=0)

    matches = query.order_by(Match.found_at.desc()).paginate(page=page, per_page=24, error_out=False)
    searches = Search.query.order_by(Search.name).all()

    return render_template(
        "matches/index.html",
        matches=matches,
        searches=searches,
        search_id=search_id,
        unseen_only=unseen_only,
    )


@matches_bp.route("/matches/<int:match_id>/seen", methods=["POST"])
def mark_seen(match_id):
    match = Match.query.get_or_404(match_id)
    match.seen = 1
    db.session.commit()
    return jsonify({"ok": True})


@matches_bp.route("/matches/dismiss-all", methods=["POST"])
def dismiss_all():
    search_id = request.form.get("search_id", type=int)
    query = Match.query.filter_by(seen=0)
    if search_id:
        query = query.filter_by(search_id=search_id)
    query.update({"seen": 1})
    db.session.commit()
    return redirect(url_for("matches.index", search_id=search_id))
