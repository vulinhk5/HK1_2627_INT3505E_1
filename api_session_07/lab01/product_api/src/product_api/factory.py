import os

from flask import Flask

from .api import register_blueprints
from .api.errors import register_error_handlers
from .config import DefaultConfig
from .extensions import db, migrate
from .logging_config import configure_logging


def create_app(config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or os.environ.get("APP_CONFIG", DefaultConfig))
    app.json.sort_keys = False
    app.url_map.strict_slashes = False  
    configure_logging(app)
    db.init_app(app)
    migrate.init_app(app, db) 
    register_error_handlers(app)
    register_blueprints(app)
    return app