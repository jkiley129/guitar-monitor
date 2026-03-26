from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from app.database import get_setting, set_setting

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "save":
            set_setting("ntfy_topic", request.form.get("ntfy_topic", "").strip())
            new_interval = request.form.get("poll_interval_minutes", "20").strip()
            set_setting("poll_interval_minutes", new_interval)

            try:
                from app.scheduler import reschedule
                reschedule(int(new_interval))
            except Exception:
                pass

            flash("Settings saved.", "success")
            return redirect(url_for("settings.index"))

        elif action == "test_notify":
            from app.notifier import send_test_notification
            ok, msg = send_test_notification()
            flash(msg, "success" if ok else "danger")
            return redirect(url_for("settings.index"))

        elif action == "poll_now":
            from app.scheduler import trigger_now
            try:
                results, sent = trigger_now(current_app._get_current_object())
                total = sum(results.values())
                if total == 0:
                    msg = "Scan complete — no new listings found this time."
                else:
                    parts = [f"{count} from \"{name}\"" for name, count in results.items() if count > 0]
                    msg = f"Found {total} new listing{'s' if total != 1 else ''}! ({', '.join(parts)})"
                    if sent:
                        msg += f" — {sent} notification{'s' if sent != 1 else ''} sent."
                flash(msg, "success" if total == 0 else "warning")
            except Exception as e:
                flash(f"Scan failed: {e}", "danger")
            return redirect(url_for("settings.index"))

    settings = {
        "ntfy_topic": get_setting("ntfy_topic", ""),
        "poll_interval_minutes": get_setting("poll_interval_minutes", "20"),
    }
    from app.models import Search
    configured = bool(settings["ntfy_topic"])
    searches_exist = Search.query.count() > 0
    return render_template("settings/index.html", settings=settings, configured=configured, searches_exist=searches_exist)
