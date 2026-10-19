import base64
import json
import os

from flask import Blueprint, jsonify, request
from jsonschema import ValidationError, validate
from sqlalchemy import select, tuple_
from sqlalchemy.exc import IntegrityError

from models import Book, Category, db

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

with open(os.path.join(os.path.dirname(__file__), "..", "schemas", "book.json")) as f:
    BOOK_SCHEMA = json.load(f)


#LAB01
def check(data):
    try:
        validate(data, BOOK_SCHEMA)
    except ValidationError as e:
        return jsonify(error="validation_error", message=e.message), 400
    if db.session.get(Category, data["category_id"]) is None:
        return jsonify(error="bad_category", message="Category does not exist"), 400
    return None


def commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="duplicate_isbn", message="ISBN already exists"), 409
    return None


def book_not_found():
    return jsonify(error="not_found", message="Book not found"), 404


@books_bp.get("")
def list_books():
    limit = max(1, min(request.args.get("limit", 20, type=int), 100))
    cat_id = request.args.get("cat_id", type=int)

    p, cols, desc = parse_sort(request.args.get("sort", "-id"))
    if p is None:                                  
        return jsonify(error=cols, message="Unsupported sort key. Use id or price, optionally prefixed with '-'"), 400

    q = select(Book).order_by(*cols)
    if cat_id:
        q = q.filter(Book.category_id == cat_id)

    q, err = apply_cursor(q, p, desc, request.args.get("cursor"))
    if err:
        return jsonify(error=err, message="Invalid cursor"), 400

    rows = db.session.scalars(q.limit(limit + 1)).all()
    return jsonify(build_response(rows, limit, p))


@books_bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return book_not_found()
    return jsonify(book.to_dict())


@books_bp.post("")
def create_book():
    data = request.get_json(silent=True)
    err = check(data)
    if err:
        return err

    book = Book(**data)
    db.session.add(book)
    err = commit()
    if err:
        return err
    return jsonify(book.to_dict()), 201


@books_bp.put("/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return book_not_found()

    data = request.get_json(silent=True)
    err = check(data)
    if err:
        return err

    for field, value in data.items():
        setattr(book, field, value)
    err = commit()
    if err:
        return err
    return jsonify(book.to_dict())


@books_bp.delete("/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return book_not_found()
    db.session.delete(book)
    db.session.commit()
    return "", 204

#LAB02
SORT = {"id": Book.id, "price": Book.price_vnd}


def parse_sort(raw):
    desc = raw.startswith("-")
    key = raw.lstrip("-")
    if key not in SORT:
        return None, "bad_sort", 400
    p = SORT[key]
    cols = [
        p.desc() if desc else p.asc(),
        Book.id.desc() if desc else Book.id.asc(),     
    ]
    return p, cols, desc


def apply_cursor(q, p, desc, cursor):
    if not cursor:
        return q, None
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor))
        value, last_id = data["v"], data["id"]
    except Exception:
        return None, "bad_cursor"
    key = tuple_(p, Book.id)                           
    q = q.where(key < (value, last_id) if desc else key > (value, last_id))
    return q, None


def build_response(rows, limit, p):
    has_more = len(rows) > limit                       
    rows = rows[:limit]
    next_cursor = None
    if has_more:
        last = rows[-1]
        raw = json.dumps({"v": getattr(last, p.key), "id": last.id})
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode()
    return {"items": [b.to_dict() for b in rows], "next_cursor": next_cursor}





