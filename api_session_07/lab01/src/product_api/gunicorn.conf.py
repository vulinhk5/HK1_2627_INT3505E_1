import os
import time

bind = "0.0.0.0:5000"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
worker_class = "sync"
timeout = 60  
graceful_timeout = 30
keepalive = 5 
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = "info"
proc_name = "product-api"


def on_starting(server):
    if os.environ.get("RUN_MIGRATIONS_ON_START", "1") != "1":
        return
    from flask_migrate import upgrade

    from product_api.factory import create_app

    app = create_app()
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
    for attempt in range(1, 11):
        try:
            with app.app_context():
                upgrade(directory=directory)
            server.log.info("database migrated to head")
            return
        except Exception as exc:  
            server.log.warning("database not ready (attempt %d/10): %s", attempt, exc)
            time.sleep(2)
    raise SystemExit("database is not reachable, giving up")
