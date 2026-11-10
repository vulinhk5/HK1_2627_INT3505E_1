from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__, url_prefix="")


@health_bp.get("/healthz")
def liveness():
    return jsonify({"status": "ok"}), 200


@health_bp.get("/ready")
def readiness():
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        db.session.rollback()
        checks["db"] = "err"
        current_app.logger.warning("readiness_check_failed", extra={"check": "db"}, exc_info=True)
    ok = all(value == "ok" for value in checks.values())
    body = {"status": "ok" if ok else "degraded", "checks": checks}
    return jsonify(body), (200 if ok else 503)
