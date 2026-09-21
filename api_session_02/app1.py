from flask import Flask, request, jsonify

app = Flask(__name__)

books = []

@app.route("/books", methods=["GET"])
def get_books():
    return jsonify({
        "data": books,
        "total": len(books)
    }), 200

@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    for book in books:
        if book["id"] == book_id:
            return jsonify(book), 200

    return jsonify({
        "error": "Book not found"
    }), 404

@app.route("/books", methods=["POST"])
def create_book():

    if not request.is_json:
        return jsonify({
            "error": "Content-Type must be json"
        }), 415

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "Invalid JSON"
        }), 400


    if "author" not in data:
        return jsonify({
            "error": "author is required"
        }), 422

    new_id = len(books) + 1

    book = {
        "id": new_id,
        "title": data["title"],
        "author": data["author"],
        "published_year": data["published_year"]
    }

    books.append(book)

    return jsonify(book), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)