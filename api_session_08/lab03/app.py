"""Books API - Flask (in-memory) dùng cho Lab 3: Newman-runnable collection.

Chạy:  python app.py   ->  http://127.0.0.1:5000
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

# "Database" trong bộ nhớ, có sẵn 1 cuốn để GET /books/{id} chạy được ngay.
BOOKS = {
    1: {"id": 1, "title": "Building Microservices", "author": "Sam Newman"},
}
_next_id = 2


def error(status, code, message):
    """Định dạng lỗi thống nhất: {"code": ..., "message": ...}."""
    return jsonify({"code": code, "message": message}), status


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/books")
def list_books():
    return jsonify(list(BOOKS.values())), 200


@app.get("/books/<int:book_id>")
def get_book(book_id):
    book = BOOKS.get(book_id)
    if book is None:
        return error(404, "NOT_FOUND", f"Book {book_id} not found")
    return jsonify(book), 200


@app.post("/books")
def create_book():
    global _next_id
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return error(400, "VALIDATION", "title is required")
    book = {"id": _next_id, "title": title.strip(), "author": data.get("author", "")}
    BOOKS[_next_id] = book
    _next_id += 1
    return jsonify(book), 201


@app.put("/books/<int:book_id>")
def update_book(book_id):
    book = BOOKS.get(book_id)
    if book is None:
        return error(404, "NOT_FOUND", f"Book {book_id} not found")
    data = request.get_json(silent=True) or {}
    title = data.get("title", book["title"])
    if not isinstance(title, str) or not title.strip():
        return error(400, "VALIDATION", "title must be a non-empty string")
    book["title"] = title.strip()
    book["author"] = data.get("author", book["author"])
    return jsonify(book), 200


@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    if book_id not in BOOKS:
        return error(404, "NOT_FOUND", f"Book {book_id} not found")
    del BOOKS[book_id]
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
