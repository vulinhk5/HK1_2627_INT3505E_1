import base64
import json
import os

from flask import Blueprint, jsonify, request
from jsonschema import ValidationError, validate
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from models import Book, Category, db

books_bp = Blueprint('books_bp', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))

schema_path = os.path.join(current_dir, '..', 'schemas', 'book.json')

with open(schema_path, 'r', encoding='utf-8') as f:
    book_schema = json.load(f)


def error(code, message, status):
    return jsonify({"error": code, "message": message}), status

#LAB02
SORT = {"id": Book.id, "price": Book.price_vnd, "title": Book.title, "stock": Book.stock}


def parse_sort(raw):
    order, seen = [], set()
    for part in raw.split(","):
        desc = part.startswith("-")
        key = part.lstrip("-")
        if key not in SORT or key in seen:
            return None, "bad_sort"
        seen.add(key)
        order.append((SORT[key], desc))
    if "id" not in seen:
        order.append((Book.id, order[0][1]))    
    return order, None


def apply_cursor(q, order, cursor):
    try:
        values = json.loads(base64.urlsafe_b64decode(cursor))
        if not isinstance(values, list) or len(values) != len(order):
            raise ValueError("cursor does not match the sort")
    except Exception:
        return None, "bad_cursor"

    conditions = []
    for i, (col, desc) in enumerate(order):
        same = [c == v for (c, _), v in zip(order[:i], values[:i])]
        after = col < values[i] if desc else col > values[i]
        conditions.append(and_(*same, after))
    return q.where(or_(*conditions)), None


def build_response(rows, limit, order):
    has_more = len(rows) > limit               
    rows = rows[:limit]
    next_cursor = None
    if has_more:
        last = rows[-1]
        raw = json.dumps([getattr(last, col.key) for col, _ in order])
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode()
    return {"strategy": "cursor", "items": [b.to_dict() for b in rows], "next_cursor": next_cursor}


# Lab 01 
def validate_book(data):
    """Return an error response if the request body is invalid, otherwise None."""
    if not isinstance(data, dict):
        return error("bad_request", "Request body must be a valid JSON object", 400)

    try:
        validate(instance=data, schema=book_schema)
    except ValidationError as e:
        return error("validation_error", e.message, 422)

    category_id = data.get('category_id')
    if category_id is not None and db.session.get(Category, category_id) is None:
        return error("bad_category", "Category does not exist", 400)

    return None


def commit_or_conflict():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("conflict", "ISBN already exists or the data violates a database constraint", 409)
    return None


def book_not_found():
    return error("not_found", "Book not found", 404)


#
@books_bp.route('', methods=['GET'])
def list_books():
    strategy = request.args.get('strategy', 'offset')
    if strategy not in ('offset', 'cursor'):
        return error("bad_strategy", "strategy must be 'offset' or 'cursor'", 400)

    limit = max(1, min(request.args.get('limit', 20, type=int), 100))

    order, err = parse_sort(request.args.get('sort', '-id'))
    if err:
        return error(err, "Unsupported sort. Allowed keys: id, price, title, stock "
                          "(comma separated, '-' prefix = descending, e.g. -price,title)", 400)

    #filters
    q = select(Book)
    genre = request.args.get('genre')
    if genre:
        q = q.join(Category).where(Category.slug == genre)
    cat_id = request.args.get('cat_id', type=int)
    if cat_id:
        q = q.where(Book.category_id == cat_id)

    order_by = [col.desc() if desc else col.asc() for col, desc in order]

    #offset
    if strategy == 'offset':
        offset = max(0, request.args.get('offset', 0, type=int))
        total = db.session.scalar(select(func.count()).select_from(q.subquery()))
        rows = db.session.scalars(q.order_by(*order_by).offset(offset).limit(limit)).all()
        return jsonify({
            "strategy": "offset",
            "items": [b.to_dict() for b in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }), 200

    # ---- strategy 2: cursor ----
    cursor = request.args.get('cursor')
    if cursor:
        q, err = apply_cursor(q, order, cursor)
        if err:
            return error(err, "Invalid cursor (it must come from the same sort that produced it)", 400)

    rows = db.session.scalars(q.order_by(*order_by).limit(limit + 1)).all()
    return jsonify(build_response(rows, limit, order)), 200


@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return book_not_found()

    return jsonify(book.to_dict()), 200


@books_bp.route('', methods=['POST'])
def create_book():
    data = request.get_json(silent=True)

    err = validate_book(data)
    if err:
        return err

    new_book = Book(
        title=data['title'],
        isbn=data.get('isbn'),
        price_vnd=data.get('price_vnd', 0),
        stock=data.get('stock', 0),
        category_id=data.get('category_id')
    )
    db.session.add(new_book)

    err = commit_or_conflict()
    if err:
        return err

    return jsonify(new_book.to_dict()), 201


@books_bp.route('/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return book_not_found()

    data = request.get_json(silent=True)

    err = validate_book(data)
    if err:
        return err

    for field in ('title', 'isbn', 'price_vnd', 'stock', 'category_id'):
        if field in data:
            setattr(book, field, data[field])

    err = commit_or_conflict()
    if err:
        return err

    return jsonify(book.to_dict()), 200


@books_bp.route('/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return book_not_found()

    db.session.delete(book)
    db.session.commit()
    return '', 204
