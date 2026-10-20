import base64

import pytest
from flask import Flask

from models import Book, Category, db
from routes.books import books_bp

URL = "/api/v1/books"


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"     
    app.config["TESTING"] = True
    db.init_app(app)
    app.register_blueprint(books_bp, url_prefix=URL)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def categories(app):
    """Two categories. Returns their ids, e.g. {"programming": 1, "fiction": 2}."""
    rows = [Category(name="Programming", slug="programming"), Category(name="Fiction", slug="fiction")]
    db.session.add_all(rows)
    db.session.commit()
    return {"programming": rows[0].id, "fiction": rows[1].id}


@pytest.fixture
def books(categories):
    """30 books. Prices, titles and stocks repeat on purpose, so sorting really needs the id tie-break.

    Returns a plain list of dicts: the "truth" that the API results are compared against.
    """
    cat_ids = list(categories.values())
    rows = [
        Book(
            title=f"Title {i % 5}",
            isbn=str(9780000000000 + i),
            price_vnd=100000 * (i % 4 + 1),
            stock=i % 3,
            category_id=cat_ids[i % 2],
        )
        for i in range(1, 31)
    ]
    db.session.add_all(rows)
    db.session.commit()
    return [
        {"id": b.id, "title": b.title, "price_vnd": b.price_vnd, "stock": b.stock, "category_id": b.category_id}
        for b in rows
    ]



def new_book(category_id, i=1, **changes):
    data = {
        "title": f"Book {i}",
        "isbn": str(9781000000000 + i),
        "price_vnd": 120000,
        "stock": 5,
        "category_id": category_id,
    }
    data.update(changes)
    return data


FIELD = {"id": "id", "price": "price_vnd", "title": "title", "stock": "stock"}


def expected_ids(books, sort, category_id=None):
    keys = [(part.lstrip("-"), part.startswith("-")) for part in sort.split(",")]
    if "id" not in [name for name, _ in keys]:
        keys.append(("id", keys[0][1]))              
    rows = [b for b in books if category_id in (None, b["category_id"])]
    for name, desc in reversed(keys):                   
        rows.sort(key=lambda b: b[FIELD[name]], reverse=desc)
    return [b["id"] for b in rows]


def walk_cursor(client, limit=7, **params):
    ids, cursor = [], None
    for _ in range(100):
        query = dict(params, strategy="cursor", limit=limit)
        if cursor:
            query["cursor"] = cursor
        body = client.get(URL, query_string=query).get_json()
        ids += [b["id"] for b in body["items"]]
        cursor = body["next_cursor"]
        if cursor is None:
            return ids
    pytest.fail("next_cursor never became null")


def walk_offset(client, limit=7, **params):
    ids, offset = [], 0
    for _ in range(100):
        query = dict(params, strategy="offset", limit=limit, offset=offset)
        body = client.get(URL, query_string=query).get_json()
        ids += [b["id"] for b in body["items"]]
        offset += limit
        if offset >= body["total"]:
            return ids
    pytest.fail("offset never reached total")


def b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode()


# Lab 01
def test_create_book(client, categories):
    r = client.post(URL, json=new_book(categories["programming"]))
    assert r.status_code == 201
    body = r.get_json()
    assert body["id"]
    assert body["title"] == "Book 1"
    assert body["price_vnd"] == 120000


def test_get_one_book(client, categories):
    created = client.post(URL, json=new_book(categories["programming"])).get_json()
    r = client.get(f"{URL}/{created['id']}")
    assert r.status_code == 200
    assert r.get_json()["title"] == "Book 1"


def test_get_missing_book_returns_404(client):
    r = client.get(f"{URL}/9999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"


def test_update_book(client, categories):
    cat = categories["programming"]
    book_id = client.post(URL, json=new_book(cat)).get_json()["id"]

    r = client.put(f"{URL}/{book_id}", json=new_book(cat, title="New title", price_vnd=150000))
    assert r.status_code == 200
    assert r.get_json()["title"] == "New title"

    saved = client.get(f"{URL}/{book_id}").get_json()          
    assert saved["price_vnd"] == 150000


def test_update_missing_book_returns_404(client, categories):
    r = client.put(f"{URL}/9999", json=new_book(categories["programming"]))
    assert r.status_code == 404


def test_delete_book(client, categories):
    book_id = client.post(URL, json=new_book(categories["programming"])).get_json()["id"]
    assert client.delete(f"{URL}/{book_id}").status_code == 204
    assert client.get(f"{URL}/{book_id}").status_code == 404


def test_delete_missing_book_returns_404(client):
    assert client.delete(f"{URL}/9999").status_code == 404


#Lab 01 error

def test_create_duplicate_isbn_returns_409(client, categories):
    data = new_book(categories["programming"])
    assert client.post(URL, json=data).status_code == 201
    r = client.post(URL, json=data)
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"


def test_update_to_another_books_isbn_returns_409(client, categories):
    cat = categories["programming"]
    client.post(URL, json=new_book(cat, i=1))
    second_id = client.post(URL, json=new_book(cat, i=2)).get_json()["id"]

    r = client.put(f"{URL}/{second_id}", json=new_book(cat, i=2, title="Changed", isbn=new_book(cat, i=1)["isbn"]))
    assert r.status_code == 409

    assert client.get(f"{URL}/{second_id}").get_json()["title"] == "Book 2"


def test_create_unknown_category_returns_400(client, categories):
    r = client.post(URL, json=new_book(9999))
    assert r.status_code == 400
    assert r.get_json()["error"] == "bad_category"


def test_update_unknown_category_returns_400(client, categories):
    book_id = client.post(URL, json=new_book(categories["programming"])).get_json()["id"]
    r = client.put(f"{URL}/{book_id}", json=new_book(9999))
    assert r.status_code == 400


def test_body_must_be_a_json_object(client):
    r = client.post(URL, json=[1, 2, 3])
    assert r.status_code == 400
    assert r.get_json()["error"] == "bad_request"


def test_malformed_json_returns_400(client):
    r = client.post(URL, data="this is not json", content_type="application/json")
    assert r.status_code == 400


def test_create_without_title_returns_422(client, categories):
    data = new_book(categories["programming"])
    del data["title"]
    r = client.post(URL, json=data)
    assert r.status_code == 422
    assert r.get_json()["error"] == "validation_error"


def test_create_with_wrong_type_returns_422(client, categories):
    r = client.post(URL, json=new_book(categories["programming"], price_vnd="abc"))
    assert r.status_code == 422

#Bai 02
def test_list_defaults(client, books):
    body = client.get(URL).get_json()
    assert body["strategy"] == "offset"                     
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["total"] == 30
    assert [b["id"] for b in body["items"]] == expected_ids(books, "-id")[:20]    


def test_limit_is_capped_at_100(client, books):
    body = client.get(URL, query_string={"limit": 1000}).get_json()
    assert body["limit"] == 100
    assert len(body["items"]) == 30


def test_limit_that_is_not_a_number_falls_back_to_default(client, books):
    body = client.get(URL, query_string={"limit": "abc"}).get_json()
    assert body["limit"] == 20


def test_offset_page_content(client, books):
    query = {"strategy": "offset", "limit": 5, "offset": 10, "sort": "price"}
    body = client.get(URL, query_string=query).get_json()
    assert [b["id"] for b in body["items"]] == expected_ids(books, "price")[10:15]
    assert body["offset"] == 10
    assert body["total"] == 30


def test_offset_past_the_end_returns_empty_page(client, books):
    body = client.get(URL, query_string={"strategy": "offset", "offset": 500}).get_json()
    assert body["items"] == []
    assert body["total"] == 30


def test_cursor_first_page_has_next_cursor(client, books):
    body = client.get(URL, query_string={"strategy": "cursor", "limit": 5, "sort": "-id"}).get_json()
    assert body["strategy"] == "cursor"
    assert len(body["items"]) == 5
    assert body["next_cursor"]


def test_cursor_last_page_has_no_next_cursor(client, books):
    body = client.get(URL, query_string={"strategy": "cursor", "limit": 30}).get_json()
    assert len(body["items"]) == 30
    assert body["next_cursor"] is None


def test_cursor_has_no_duplicates_or_gaps_when_prices_are_equal(client, books):
    ids = walk_cursor(client, sort="price")                  # only 4 different prices for 30 books
    assert len(ids) == len(set(ids)) == 30


def test_cursor_is_stable_when_a_book_is_inserted_between_pages(client, books, categories):
    query = {"strategy": "cursor", "limit": 5, "sort": "-id"}
    first = client.get(URL, query_string=query).get_json()

    client.post(URL, json=new_book(categories["programming"]))        

    second = client.get(URL, query_string=dict(query, cursor=first["next_cursor"])).get_json()
    first_ids = [b["id"] for b in first["items"]]
    second_ids = [b["id"] for b in second["items"]]
    assert not set(first_ids) & set(second_ids)         
    assert second_ids[0] == first_ids[-1] - 1               



SORTS = ["id", "-id", "price", "-price", "title", "stock", "-price,title", "price,-title", "-stock,title,-price"]


@pytest.mark.parametrize("sort", SORTS)
def test_sort_with_cursor(client, books, sort):
    assert walk_cursor(client, sort=sort) == expected_ids(books, sort)


@pytest.mark.parametrize("sort", SORTS)
def test_sort_with_offset(client, books, sort):
    assert walk_offset(client, sort=sort) == expected_ids(books, sort)


@pytest.mark.parametrize("walk", [walk_cursor, walk_offset])
def test_genre_filter(client, books, categories, walk):
    fiction = categories["fiction"]
    ids = walk(client, sort="-price,title", genre="fiction")
    assert ids == expected_ids(books, "-price,title", category_id=fiction)
    assert len(ids) == 15


def test_unknown_genre_returns_empty_page(client, books):
    body = client.get(URL, query_string={"genre": "no-such-genre"}).get_json()
    assert body["items"] == []
    assert body["total"] == 0


def test_cat_id_filter(client, books, categories):
    fiction = categories["fiction"]
    body = client.get(URL, query_string={"cat_id": fiction, "limit": 100}).get_json()
    assert [b["id"] for b in body["items"]] == expected_ids(books, "-id", category_id=fiction)
    assert body["total"] == 15



@pytest.mark.parametrize("params, error", [
    ({"strategy": "foo"}, "bad_strategy"),
    ({"sort": "foo"}, "bad_sort"),
    ({"sort": ""}, "bad_sort"),
    ({"sort": "price,price"}, "bad_sort"),                    
    ({"sort": "-price,genre"}, "bad_sort"),                  
    ({"strategy": "cursor", "cursor": "garbage"}, "bad_cursor"),
    ({"strategy": "cursor", "cursor": b64('{"a": 1}')}, "bad_cursor"),  
])
def test_bad_query_params_return_400(client, books, params, error):
    r = client.get(URL, query_string=params)
    assert r.status_code == 400
    assert r.get_json()["error"] == error


def test_cursor_from_another_sort_returns_400(client, books):
    first = client.get(URL, query_string={"strategy": "cursor", "limit": 5, "sort": "price"}).get_json()
    r = client.get(URL, query_string={"strategy": "cursor", "sort": "-price,title", "cursor": first["next_cursor"]})
    assert r.status_code == 400
    assert r.get_json()["error"] == "bad_cursor"
