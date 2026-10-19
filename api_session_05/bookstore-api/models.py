from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()

book_author = db.Table('book_author',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    
    books = db.relationship('Book', backref='category', lazy=True)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(100))

    reviews = db.relationship('Review', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    price_vnd = db.Column(db.Integer)
    stock = db.Column(db.Integer)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    authors = db.relationship('Author', secondary=book_author, backref=db.backref('books', lazy=True))

    def to_dict(self):
        return {"id": f"book_{self.id}", "title": self.title}

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    book = db.relationship('Book', backref=db.backref('reviews', lazy=True))