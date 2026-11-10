import pytest
from sqlalchemy.exc import InvalidRequestError

from conftest import assert_error
from product_api.extensions import db
from product_api.models import Order, OrderItem, Product

URL = "/api/v1/orders"


def _place_order(client, products, qty=1, customer="Linh"):
    payload = {
        "customer_name": customer,
        "items": [{"product_id": p["id"], "qty": qty} for p in products],
    }
    response = client.post(URL, json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()

def test_create_order_with_multiple_products(client, make_product):
    pen = make_product(price_cents=5000)
    book = make_product(price_cents=12000)
    response = client.post(
        URL,
        json={
            "customer_name": "Linh",
            "items": [
                {"product_id": pen["id"], "qty": 2},
                {"product_id": book["id"], "qty": 1},
            ],
        },
    )
    assert response.status_code == 201
    assert response.headers["Location"].startswith(URL + "/")
    body = response.get_json()
    assert body["customer_name"] == "Linh"
    assert len(body["items"]) == 2 
    assert body["total_cents"] == 2 * 5000 + 12000
    first = body["items"][0]
    assert first["product"] == {"id": pen["id"], "sku": pen["sku"], "name": pen["name"]}
    assert first["unit_price_cents"] == 5000 and first["line_total_cents"] == 10000


def test_order_keeps_price_snapshot_when_product_price_changes(client, make_product):
    pen = make_product(price_cents=5000)
    order = _place_order(client, [pen], qty=2)
    client.patch(f"/api/v1/products/{pen['id']}", json={"price_cents": 9999})
    again = client.get(f"{URL}/{order['id']}").get_json()
    assert again["items"][0]["unit_price_cents"] == 5000
    assert again["total_cents"] == 10000


def test_create_order_validation_errors(client, make_product):
    pen = make_product()
    ok_item = {"product_id": pen["id"], "qty": 1}
    cases = [
        {"customer_name": "Linh", "items": []},  
        {"customer_name": "Linh"}, 
        {"items": [ok_item]},  
        {"customer_name": "Linh", "items": [{"product_id": pen["id"], "qty": 0}]},
        {"customer_name": "Linh", "items": [{"product_id": pen["id"]}]},
        {"customer_name": "Linh", "items": [ok_item, ok_item]},  
    ]
    for payload in cases:
        assert_error(client.post(URL, json=payload), 422, "validation_error")


def test_create_order_with_unknown_or_archived_product_returns_422(client, make_product):
    pen = make_product()
    gone = make_product()
    client.delete(f"/api/v1/products/{gone['id']}")
    for bad_id in (9999, gone["id"]):
        response = client.post(
            URL,
            json={
                "customer_name": "Linh",
                "items": [{"product_id": pen["id"], "qty": 1}, {"product_id": bad_id, "qty": 1}],
            },
        )
        assert_error(response, 422, "unknown_product")
    assert client.get(URL).get_json()["total"] == 0 

def test_get_order_and_404(client, make_product):
    order = _place_order(client, [make_product(), make_product()])
    assert client.get(f"{URL}/{order['id']}").get_json() == order
    assert_error(client.get(f"{URL}/9999"), 404, "not_found")


def test_list_orders_pagination_shape(client, make_product):
    pen = make_product()
    for _ in range(3):
        _place_order(client, [pen])
    body = client.get(f"{URL}?page=2&size=2").get_json()
    assert set(body) == {"items", "page", "size", "total"}
    assert body["total"] == 3 and len(body["items"]) == 1


def test_list_orders_uses_eager_loading_no_n_plus_one(client, make_product, count_queries):
    """Số query của GET /orders không đổi dù có 2 hay 12 đơn (mỗi đơn 3 dòng)."""
    products = [make_product() for _ in range(3)]
    for _ in range(2):
        _place_order(client, products)

    with count_queries() as small:
        response = client.get(f"{URL}?size=100")
    assert response.status_code == 200 and len(response.get_json()["items"]) == 2

    for _ in range(10):
        _place_order(client, products)

    with count_queries() as big:
        response = client.get(f"{URL}?size=100")
    assert response.status_code == 200 and len(response.get_json()["items"]) == 12

    assert len(big) == len(small) == 3, big


def test_get_order_uses_constant_number_of_queries(client, make_product, count_queries):
    products = [make_product() for _ in range(6)]
    order = _place_order(client, products)
    with count_queries() as queries:
        response = client.get(f"{URL}/{order['id']}")
    assert len(response.get_json()["items"]) == 6
    assert len(queries) == 2  

def test_lazy_loading_raises_instead_of_silent_n_plus_one(app):
    with app.app_context():
        product = Product(sku="SKU-LZ", name="Lazy", price_cents=100)
        order = Order(customer_name="Linh")
        order.items.append(OrderItem(product=product, qty=1, unit_price_cents=100))
        db.session.add(order)
        db.session.commit()
        db.session.expire_all()
        loaded = db.session.get(Order, order.id)
        with pytest.raises(InvalidRequestError):
            loaded.items  


def test_add_item_to_existing_order(client, make_product):
    pen, book = make_product(price_cents=100), make_product(price_cents=250)
    order = _place_order(client, [pen])
    response = client.post(f"{URL}/{order['id']}/items", json={"product_id": book["id"], "qty": 3})
    assert response.status_code == 201
    body = response.get_json()
    assert [i["product_id"] for i in body["items"]] == [pen["id"], book["id"]]
    assert body["total_cents"] == 100 + 3 * 250


def test_add_item_errors(client, make_product):
    pen, other = make_product(), make_product()
    order = _place_order(client, [pen])
    target = f"{URL}/{order['id']}/items"
    assert_error(client.post(target, json={"product_id": pen["id"], "qty": 1}), 409, "duplicate_item")
    assert_error(client.post(target, json={"product_id": 9999, "qty": 1}), 422, "unknown_product")
    assert_error(client.post(target, json={"product_id": other["id"], "qty": 0}), 422, "validation_error")
    assert_error(
        client.post(f"{URL}/9999/items", json={"product_id": other["id"], "qty": 1}), 404, "not_found"
    )


def test_remove_item(client, make_product):
    pen, book = make_product(), make_product()
    order = _place_order(client, [pen, book])
    item_id = order["items"][0]["id"]
    response = client.delete(f"{URL}/{order['id']}/items/{item_id}")
    assert response.status_code == 204
    remaining = client.get(f"{URL}/{order['id']}").get_json()["items"]
    assert [i["product_id"] for i in remaining] == [book["id"]]

    last_id = remaining[0]["id"]
    assert_error(client.delete(f"{URL}/{order['id']}/items/{last_id}"), 409, "order_requires_item")
    assert_error(client.delete(f"{URL}/{order['id']}/items/9999"), 404, "not_found")
