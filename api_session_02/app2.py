from flask import Flask, request, jsonify, make_response
from data import BOOKS

app = Flask(__name__)


def find_by_id(book_id):
    return next((book for book in BOOKS if book["id"] == book_id), None)


# GET
@app.get("/books/<int:book_id>")
def fetch_book(book_id):
    book = find_by_id(book_id)

    if book is None:
        return jsonify({"error": "not found"}), 404

    resp = make_response(jsonify(book), 200)
    resp.headers["Cache-Control"] = "max-age=60"

    return resp


# PUT - thay toàn bộ
@app.put("/books/<int:book_id>")
def put_book(book_id):
    book = find_by_id(book_id)

    if book is None:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(silent=True) or {}

    title = data.get("title")
    author = data.get("author")

    if not title or not author:
        return jsonify({"error": "need title+author"}), 422

    BOOKS[BOOKS.index(book)] = {
        "id": book_id,
        "title": title.strip(),
        "author": author.strip(),
        "isbn": data.get("isbn"),
        "price": data.get("price")
    }

    return jsonify(BOOKS[BOOKS.index(book)]), 200


# PATCH - chỉ cập nhật field có trong body
@app.patch("/books/<int:book_id>")
def patch_book(book_id):
    book = find_by_id(book_id)

    if book is None:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(silent=True) or {}

    if not data:
        return jsonify({"error": "no fields"}), 422

    for field in data:
        if field not in ("title", "author", "isbn", "price"):
            return jsonify({"error": f"Unsupported field: {field}"}), 422

    if "price" in data:
        price = data["price"]

        if type(price) not in (int, float) or price <= 0:
            return jsonify({"error": "price must be positive"}), 422

    for field in ["title", "author", "isbn"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return jsonify({"error": f"Invalid {field}"}), 422

            data[field] = data[field].strip()

    book.update(data)

    return jsonify(book), 200


# DELETE - idempotent
@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    book = find_by_id(book_id)

    if book is None:
        return jsonify({"error": "not found"}), 404

    BOOKS.remove(book)

    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)