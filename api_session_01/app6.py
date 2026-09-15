from flask import Flask, jsonify, request

app = Flask(__name__)

# Pre-populated with your requested books
_next = 8
BOOKS = [
    {"id": 1, "title": "Demain", "author": "Hermann Hesse", "year": 1919},
    {"id": 2, "title": "Into the Magic Shop", "author": "James R. Doty", "year": 2016},
    {"id": 3, "title": "A Little Life", "author": "Hanya Yanagihara", "year": 2015},
    {"id": 4, "title": "Jane Eyre", "author": "Charlotte Brontë", "year": 1847},
    {"id": 5, "title": "The Green Mile", "author": "Stephen King", "year": 1996},
    {"id": 6, "title": "Romeo and Juliet", "author": "William Shakespeare", "year": 1597},
    {"id": 7, "title": "Ruby Red Trilogy", "author": "Kerstin Gier", "year": 2009}
]

def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)

# -------------------------------------------------------------
# 1. LIST + SEARCH (?q=...) + SORT (?sort=title)
# -------------------------------------------------------------
@app.route("/books", methods=["GET"])
def list_books():
    n = int(request.args.get("limit", 100))
    q = request.args.get("q", "").lower()
    sort_by = request.args.get("sort")
    
    # Create a working copy of the list to filter/sort
    results = BOOKS.copy()
    
    # (a) Search functionality: look in title or author
    if q:
        results = [
            b for b in results 
            if q in b["title"].lower() or q in b["author"].lower()
        ]
        
    # (b) Sort functionality: sort alphabetically by title
    if sort_by == "title":
        results = sorted(results, key=lambda x: x["title"].lower())
        
    return jsonify(results[:n]), 200

# -------------------------------------------------------------
# 2. DETAIL
# -------------------------------------------------------------
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book: 
        return {"error": "not found"}, 404
    return jsonify(book), 200

# -------------------------------------------------------------
# 3. CREATE + VALIDATION (year >= 1900)
# -------------------------------------------------------------
@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t = body.get("title")
    a = body.get("author")
    y = body.get("year")
    
    # Validate required fields
    if not t or not a:
        return {"error": "need title+author"}, 400
        
    # (c) Validate 'year' is present, is a number, and >= 1900
    if y is None:
        return {"error": "need year"}, 400
    try:
        y = int(y)
        if y < 1900:
            return {"error": "year must be >= 1900"}, 400
    except ValueError:
        return {"error": "year must be a valid number"}, 400
        
    book = {"id": _next, "title": t, "author": a, "year": y}
    _next += 1
    BOOKS.append(book)
    
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

# -------------------------------------------------------------
# 4. UPDATE + VALIDATION (year >= 1900)
# -------------------------------------------------------------
@app.route("/books/<int:bid>", methods=["PUT"])
def update_book(bid):
    book = find(bid)
    if not book: 
        return {"error": "not found"}, 404
        
    body = request.get_json(silent=True) or {}
    
    # If the user tries to update the year, validate it
    if "year" in body:
        try:
            y = int(body["year"])
            if y < 1900:
                return {"error": "year must be >= 1900"}, 400
            body["year"] = y
        except ValueError:
            return {"error": "year must be a valid number"}, 400

    # Update other fields (like title or author) if they are in the request
    for key in ["title", "author"]:
        if key in body:
            book[key] = body[key]

    return jsonify(book), 200

# -------------------------------------------------------------
# 5. DELETE
# -------------------------------------------------------------
@app.route("/books/<int:bid>", methods=["DELETE"])
def delete_book(bid):
    book = find(bid)
    if not book: 
        return {"error": "not found"}, 404
        
    BOOKS.remove(book)
    return "", 204 

if __name__ == "__main__":
    app.run(debug=True)