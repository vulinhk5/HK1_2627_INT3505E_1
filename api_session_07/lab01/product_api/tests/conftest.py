import itertools
from contextlib import contextmanager

import pytest
from sqlalchemy import event

from product_api.config import TestConfig
from product_api.extensions import db
from product_api.factory import create_app


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_product(client):
    counter = itertools.count(1)

    def _make(**overrides):
        n = next(counter)
        payload = {
            "sku": f"SKU-{n:04d}",
            "name": f"Product {n}",
            "price_cents": 1000 * n,
            "qty_in_stock": 10,
        }
        payload.update(overrides)
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return _make


@pytest.fixture()
def count_queries(app):
    @contextmanager
    def _count():
        statements = []

        def _before(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        with app.app_context():
            engine = db.engine
        event.listen(engine, "before_cursor_execute", _before)
        try:
            yield statements
        finally:
            event.remove(engine, "before_cursor_execute", _before)

    return _count


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.get_json()
    assert body["error"] == code and body["code"] == code
    assert isinstance(body["detail"], str) and body["detail"]
    assert body["message"] == body["detail"]
    return body
