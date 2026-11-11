"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
import copy
 
import pytest
from jsonschema import ValidationError, validate
 
from tools import get_book_schema
 
def test_list_books_empty_database_returns_empty_list(client):
    response = client.get("/books")
 
    assert response.status_code == 200
    assert response.get_json() == []
 
def test_get_missing_book_returns_404_not_found(client):
    response = client.get("/books/9999")
 
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"
 

def test_create_book_without_title_returns_400_with_title_error(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})
 
    assert response.status_code == 400
    body = response.get_json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "title" in {error["field"] for error in body["errors"]}
 
 
def test_deleted_book_can_no_longer_be_fetched(client):
    created = client.post(
        "/books", json={"title": "API Design Patterns", "author": "J.J. Geewax"}
    )
    assert created.status_code == 201
    book_id = created.get_json()["id"]
 
    deleted = client.delete(f"/books/{book_id}")
    assert deleted.status_code == 204
    assert deleted.data == b"" 
 
    fetched = client.get(f"/books/{book_id}")
    assert fetched.status_code == 404
    assert fetched.get_json()["code"] == "NOT_FOUND"
 
def _to_json_schema(openapi_schema):
    schema = copy.deepcopy(openapi_schema)
    for prop in schema["properties"].values():
        if prop.pop("nullable", False):
            prop["type"] = [prop["type"], "null"]
    return schema
 
 
def test_book_response_matches_schema_and_unknown_field_is_rejected(client):
    created = client.post(
        "/books",
        json={"title": "API Design Patterns", "author": "J.J. Geewax",
              "isbn": "9781617295850"},
    )
    assert created.status_code == 201
    response = client.get(f"/books/{created.get_json()['id']}")
    assert response.status_code == 200
    book = response.get_json()
 
    schema = _to_json_schema(get_book_schema())
 
    validate(instance=book, schema=schema)
 
    tampered = copy.deepcopy(book)
    tampered["unexpected_field"] = "should not be here"
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=tampered, schema=schema)
    assert excinfo.value.validator == "additionalProperties"
 
    assert "unexpected_field" not in book
    validate(instance=book, schema=schema)
 