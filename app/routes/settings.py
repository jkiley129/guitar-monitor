from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from app.database import get_setting, set_setting

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "save":
            set_setting("telegram_token", request.form.get("telegram_token", "").strip())
            set_setting("telegram_chat_id", request.form.get("telegram_chat_id", "").strip())
            new_interval = request.form.get("poll_interval_minutes", "20").strip()
            set_setting("poll_interval_minutes", new_interval)

            try:
                from app.scheduler import reschedule
                reschedule(int(new_interval))
            except Exception:
                pass

            flash("Settings saved.", "success")
            return redirect(url_for("settings.index"))

        elif action == "test_telegram":
            from app.notifier import send_test_message
            ok, msg = send_test_message()
            flash(msg, "success" if ok else "danger")
            return redirect(url_for("settings.index"))

        elif action == "poll_now":
            from app.scheduler import trigger_now
            try:
                trigger_now(current_app._get_current_object())
                flash("Poll complete — check the Matches page for new results.", "success")
            except Exception as e:
                flash(f"Poll failed: {e}", "danger")
            return redirect(url_for("settings.index"))

    settings = {
        "telegram_token": get_setting("telegram_token", ""),
        "telegram_chat_id": get_setting("telegram_chat_id", ""),
        "poll_interval_minutes": get_setting("poll_interval_minutes", "20"),
    }
    return render_template("settings/index.html", settings=settings)
