from product_api.extensions import db


def test_liveness_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_ok_when_db_reachable(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "checks": {"db": "ok"}}


def test_readiness_returns_503_when_db_down_but_liveness_stays_ok(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(db.session, "execute", boom)

    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "degraded", "checks": {"db": "err"}}

    assert client.get("/healthz").status_code == 200
