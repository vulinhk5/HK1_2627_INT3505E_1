from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

book_author = db.Table(
    "book_author",
    db.Column("book_id", db.ForeignKey("book.id"), primary_key=True),
    db.Column("author_id", db.ForeignKey("author.id"), primary_key=True),
)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), nullable=False, unique=True)
    price_vnd = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.ForeignKey("category.id"), nullable=False)

    category = db.relationship("Category", backref="books")                      
    authors = db.relationship("Author", secondary=book_author, backref="books")  

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "price_vnd": self.price_vnd,
            "stock": self.stock,
            "category_id": self.category_id,
        }


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.ForeignKey("book.id"), nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    book = db.relationship("Book", backref=db.backref("reviews", cascade="all, delete-orphan"))
    user = db.relationship("User", backref="reviews")
