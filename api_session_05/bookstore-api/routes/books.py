import json
import os
from flask import Blueprint, request, jsonify
from jsonschema import validate, ValidationError
from models import db, Book

books_bp = Blueprint('books_bp', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))

schema_path = os.path.join(current_dir, '..', 'schemas', 'book.json')

with open(schema_path, 'r', encoding='utf-8') as f:
    book_schema = json.load(f)


@books_bp.route('', methods=['GET'])
def get_all_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books]), 200

@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    return jsonify(book.to_dict()), 200

@books_bp.route('', methods=['POST'])
def create_book():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Data JSON is invalid"}), 400

    try:
        validate(instance=data, schema=book_schema)
    except ValidationError as e:
        return jsonify({
            "error": "Unprocessable Entity",
            "message": e.message
        }), 422

    new_book = Book(
        title=data['title'],
        isbn=data.get('isbn'), 
        price_vnd=data.get('price_vnd', 0),
        stock=data.get('stock', 0),
        category_id=data.get('category_id')
    )
    
    db.session.add(new_book)
    db.session.commit()

    return jsonify(new_book.to_dict()), 201