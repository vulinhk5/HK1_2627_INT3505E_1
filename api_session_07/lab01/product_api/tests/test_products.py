from conftest import assert_error

URL = "/api/v1/products"

def test_create_product_returns_201_and_location(client):
    response = client.post(
        URL, json={"sku": "ABC-1", "name": "Bút bi", "price_cents": 5000}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["sku"] == "ABC-1"
    assert body["name"] == "Bút bi"
    assert body["price_cents"] == 5000
    assert body["qty_in_stock"] == 0 
    assert body["archived"] is False
    assert body["description"] is None
    assert response.headers["Location"].endswith(f"{URL}/{body['id']}")


def test_create_product_duplicate_sku_returns_409(client, make_product):
    make_product(sku="DUP-1")
    response = client.post(URL, json={"sku": "DUP-1", "name": "X", "price_cents": 1})
    assert_error(response, 409, "conflict")


def test_create_product_validation_returns_422(client):
    cases = [
        {"sku": "ab", "name": "X", "price_cents": 1},  
        {"sku": "x" * 33, "name": "X", "price_cents": 1},  
        {"sku": "ABC", "name": "", "price_cents": 1},  
        {"sku": "ABC", "name": "n" * 256, "price_cents": 1}, 
        {"sku": "ABC", "name": "   ", "price_cents": 1}, 
        {"sku": "ABC", "name": "X", "price_cents": -1},
        {"sku": "ABC", "name": "X"},
        {"sku": "ABC", "name": "X", "price_cents": "10"}, 
        {"sku": "ABC", "name": "X", "price_cents": 1, "qty_in_stock": -5},
        {"sku": "ABC", "name": "X", "price_cents": 1, "unknown": 1},  
    ]
    for payload in cases:
        response = client.post(URL, json=payload)
        body = assert_error(response, 422, "validation_error")
        assert body["errors"], payload


def test_create_product_bad_json_returns_400(client):
    response = client.post(URL, data="{ bad json", content_type="application/json")
    assert_error(response, 400, "bad_request")
    response = client.post(URL, json=[1, 2, 3])  
    assert_error(response, 400, "bad_request")

def test_list_products_pagination_shape(client, make_product):
    for _ in range(5):
        make_product()
    response = client.get(f"{URL}?page=2&size=2")
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"items", "page", "size", "total"}
    assert body["page"] == 2 and body["size"] == 2 and body["total"] == 5
    assert [p["sku"] for p in body["items"]] == ["SKU-0003", "SKU-0004"]


def test_list_products_defaults_and_bounds(client, make_product):
    make_product()
    body = client.get(URL).get_json()
    assert body["page"] == 1 and body["size"] == 20
    assert client.get(f"{URL}?size=100000").get_json()["size"] == 100  
    assert client.get(f"{URL}?page=0&size=0").get_json()["page"] == 1
    assert_error(client.get(f"{URL}?page=abc"), 422, "validation_error")


def test_list_products_excludes_archived(client, make_product):
    keep = make_product()
    gone = make_product()
    assert client.delete(f"{URL}/{gone['id']}").status_code == 204
    body = client.get(URL).get_json()
    assert body["total"] == 1
    assert [p["id"] for p in body["items"]] == [keep["id"]]

def test_get_product(client, make_product):
    created = make_product()
    response = client.get(f"{URL}/{created['id']}")
    assert response.status_code == 200
    assert response.get_json() == created


def test_get_product_not_found_returns_404(client):
    assert_error(client.get(f"{URL}/9999"), 404, "not_found")


def test_patch_changes_only_given_fields(client, make_product):
    created = make_product(description="mô tả cũ")
    response = client.patch(f"{URL}/{created['id']}", json={"name": "Tên mới"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Tên mới"
    for untouched in ("sku", "price_cents", "qty_in_stock", "description"):
        assert body[untouched] == created[untouched]


def test_patch_can_update_price_and_clear_description(client, make_product):
    created = make_product(description="x")
    body = client.patch(
        f"{URL}/{created['id']}", json={"price_cents": 0, "description": None}
    ).get_json()
    assert body["price_cents"] == 0 and body["description"] is None


def test_patch_rejects_sku_and_invalid_values(client, make_product):
    created = make_product()
    target = f"{URL}/{created['id']}"
    assert_error(client.patch(target, json={"sku": "NEW-SKU"}), 422, "validation_error")
    assert_error(client.patch(target, json={"price_cents": -1}), 422, "validation_error")
    assert_error(client.patch(target, json={"name": ""}), 422, "validation_error")
    assert_error(client.patch("/api/v1/products/9999", json={"name": "x"}), 404, "not_found")

def test_delete_is_soft_delete(client, make_product, app):
    created = make_product()
    response = client.delete(f"{URL}/{created['id']}")
    assert response.status_code == 204 and response.data == b""
    assert_error(client.get(f"{URL}/{created['id']}"), 404, "not_found")
    assert_error(client.delete(f"{URL}/{created['id']}"), 404, "not_found")
    from product_api.extensions import db
    from product_api.models import Product

    with app.app_context():
        row = db.session.get(Product, created["id"])
        assert row is not None and row.archived is True

def test_reserve_decrements_stock(client, make_product):
    created = make_product(qty_in_stock=5)
    response = client.post(f"{URL}/{created['id']}/reserve", json={"qty": 2})
    assert response.status_code == 200
    assert response.get_json()["qty_in_stock"] == 3
    assert client.get(f"{URL}/{created['id']}").get_json()["qty_in_stock"] == 3


def test_reserve_exactly_remaining_stock_reaches_zero(client, make_product):
    created = make_product(qty_in_stock=3)
    response = client.post(f"{URL}/{created['id']}/reserve", json={"qty": 3})
    assert response.get_json()["qty_in_stock"] == 0


def test_reserve_more_than_stock_returns_409_and_keeps_stock(client, make_product):
    created = make_product(qty_in_stock=2)
    response = client.post(f"{URL}/{created['id']}/reserve", json={"qty": 3})
    body = assert_error(response, 409, "out_of_stock")
    assert "2" in body["detail"]
    assert client.get(f"{URL}/{created['id']}").get_json()["qty_in_stock"] == 2  


def test_reserve_validation_and_not_found(client, make_product):
    created = make_product()
    target = f"{URL}/{created['id']}/reserve"
    assert_error(client.post(target, json={"qty": 0}), 422, "validation_error")
    assert_error(client.post(target, json={"qty": -1}), 422, "validation_error")
    assert_error(client.post(target, json={}), 422, "validation_error")
    assert_error(client.post(target, json={"qty": "1"}), 422, "validation_error")
    assert_error(client.post(f"{URL}/9999/reserve", json={"qty": 1}), 404, "not_found")


def test_reserve_archived_product_returns_404(client, make_product):
    created = make_product()
    client.delete(f"{URL}/{created['id']}")
    assert_error(client.post(f"{URL}/{created['id']}/reserve", json={"qty": 1}), 404, "not_found")

def test_unknown_route_and_wrong_method_return_json_errors(client):
    assert_error(client.get("/api/v1/nope"), 404, "not_found")
    response = client.put(URL, json={})
    assert_error(response, 405, "method_not_allowed")
    assert "GET" in response.headers["Allow"]


def test_every_response_has_request_id_header(client):
    response = client.get(URL, headers={"X-Request-Id": "abc-123"})
    assert response.headers["X-Request-Id"] == "abc-123"
    assert client.get(URL).headers["X-Request-Id"] 
