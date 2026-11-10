import json
import logging
import re
import sys
import time
import uuid

from flask import g, has_request_context, request

HEALTH_PATHS = {"/healthz", "/ready"}
_REQUEST_ID_RE = re.compile(r"[\w.\-]{1,64}")
_RESERVED = set(vars(logging.LogRecord("x", 0, "x", 0, "x", None, None))) | {
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    converter = time.gmtime  

    def format(self, rec):
        payload = {
            "ts": self.formatTime(rec, "%Y-%m-%dT%H:%M:%SZ"),
            "level": rec.levelname,
            "event": rec.getMessage(),
        }
        if has_request_context():
            payload["request_id"] = g.get("request_id", "-")
        for key, value in rec.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if rec.exc_info:
            payload["exc"] = self.formatException(rec.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]  
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.propagate = False

    @app.before_request
    def _start_request():
        g.t0 = time.perf_counter()
        rid = request.headers.get("X-Request-Id", "")
        g.request_id = rid if _REQUEST_ID_RE.fullmatch(rid) else uuid.uuid4().hex[:16]

    @app.after_request
    def _finish_request(response):
        response.headers["X-Request-Id"] = g.get("request_id", "-")
        if request.path not in HEALTH_PATHS:
            ms = int((time.perf_counter() - g.get("t0", time.perf_counter())) * 1000)
            app.logger.info(
                "request_done",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "ms": ms,
                },
            )
        return response
