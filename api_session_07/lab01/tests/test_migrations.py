from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect

from product_api.config import TestConfig
from product_api.extensions import db
from product_api.factory import create_app

MIGRATIONS_DIR = str(Path(__file__).resolve().parent.parent / "migrations")


def _app_with_file_db(tmp_path):
    class Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'migrations.db'}"

    return create_app(Config)


def test_upgrade_creates_all_tables_and_matches_models(tmp_path):
    app = _app_with_file_db(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS_DIR)
        tables = set(inspect(db.engine).get_table_names())
        assert {"products", "orders", "order_items", "alembic_version"} <= tables

        with db.engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), db.metadata)
        assert diff == []


def test_downgrade_removes_everything(tmp_path):
    app = _app_with_file_db(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS_DIR)
        downgrade(directory=MIGRATIONS_DIR, revision="base")
        tables = set(inspect(db.engine).get_table_names())
        assert not tables & {"products", "orders", "order_items"}
