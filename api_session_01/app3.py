from flask import Flask, request, jsonify
app = Flask(__name__)

#mock data
BOOKS = [
    {
        "id": "book-01", 
        "title": "The Ones Who Walk Away from Omelas", 
        "author": "Ursula K. Le Guin"
    },
    {
        "id": "book-02", 
        "title": "Demian", 
        "author": "Hermann Hesse"
    },
    {
        "id": "book-03", 
        "title": "Into the Magic Shop", 
        "author": "James R. Doty"
    },
    {
        "id": "book-04", 
        "title": "The Little Prince", 
        "author": "Antoine de Saint-Exupéry"
    }
]

#hàm tím sách theo id
def find_by_id(book_id):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    return None

@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book), 200

@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify ({"id": item_id}), 200

@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["title"].lower()]
    return jsonify({"items": items}), 200

if __name__ == "__main__":
    app.run(debug=True)
