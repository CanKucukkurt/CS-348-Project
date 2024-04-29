from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    author_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    books = db.relationship('Book', backref='author', lazy='dynamic')
    
    __table_args__ = (
        db.Index('idx_author_last_name', 'last_name'),
    )

class Publisher(db.Model):
    publisher_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    books = db.relationship('Book', backref='publisher', lazy='dynamic')

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'), nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.publisher_id'), nullable=False)
    publication_year = db.Column(db.Integer)
    loans = db.relationship('Loan', backref='book', lazy='dynamic')
    
    __table_args__ = (
        db.Index('idx_book_title', 'title'),
    )

class Borrower(db.Model):
    borrower_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    loans = db.relationship('Loan', backref='borrower', lazy='dynamic')

class Loan(db.Model):
    loan_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrower.borrower_id'), nullable=False)
    borrowed_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date)
    
    __table_args__ = (
        db.Index('idx_loan_borrowed_date', 'borrowed_date'),
        db.Index('idx_loan_due_date', 'due_date'),
        db.Index('idx_loan_book_id', 'book_id'),
    )