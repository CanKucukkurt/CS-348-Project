import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date, timedelta
from sqlalchemy import text

app = Flask(__name__)

# Configure the connection details
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://can:can@35.225.16.213/db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class Author(db.Model):
    author_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    books = db.relationship('Book', backref='author', lazy='dynamic')

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
    status = db.Column(db.String(20), nullable=False, default='available')
    loans = db.relationship('Loan', backref='book', lazy='dynamic')

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

@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author_first_name = request.form['author_first_name']
        author_last_name = request.form['author_last_name']
        publisher_name = request.form['publisher_name']
        publisher_address = request.form['publisher_address']
        
        # Convert publication_year to an integer
        publication_year = int(request.form['publication_year'])

        # Check if author exists, if not, create a new one
        author_query = text("""
            SELECT author_id 
            FROM author
            WHERE first_name = :first_name AND last_name = :last_name
        """)
        author_result = db.session.execute(author_query, {'first_name': author_first_name, 'last_name': author_last_name}).fetchone()
        if not author_result:
            author = Author(first_name=author_first_name, last_name=author_last_name)
            db.session.add(author)
            db.session.commit()
            author_id = author.author_id
        else:
            author_id = author_result.author_id

        # Check if publisher exists, if not, create a new one
        publisher_query = text("""
            SELECT publisher_id 
            FROM publisher
            WHERE name = :name
        """)
        publisher_result = db.session.execute(publisher_query, {'name': publisher_name}).fetchone()
        if not publisher_result:
            publisher = Publisher(name=publisher_name, address=publisher_address)
            db.session.add(publisher)
            db.session.commit()
            publisher_id = publisher.publisher_id
        else:
            publisher_id = publisher_result.publisher_id

        book = Book(title=title, author_id=author_id, publisher_id=publisher_id, publication_year=publication_year)
        db.session.add(book)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_book.html')

@app.route('/authors', methods=['GET', 'POST'])
def authors():
    if request.method == 'POST':
        author_id = request.form['author_id']
        stmt = text("""
            SELECT a.author_id, a.first_name, a.last_name,
                   b.book_id, b.title, b.publication_year
            FROM author a
            LEFT JOIN book b ON a.author_id = b.author_id
            WHERE a.author_id = :author_id
        """)
        result = db.session.execute(stmt, {'author_id': author_id}).fetchall()
        if result:
            selected_author = {
                'author_id': result[0].author_id,
                'first_name': result[0].first_name,
                'last_name': result[0].last_name,
                'books': [{'book_id': row.book_id, 'title': row.title, 'publication_year': row.publication_year}
                          for row in result if row.book_id is not None]
            }
        else:
            selected_author = None
    else:
        selected_author = None

    stmt = text("SELECT * FROM author")
    authors = db.session.execute(stmt).fetchall()

    return render_template('authors.html', authors=authors, selected_author=selected_author)

@app.route('/edit', methods=['GET', 'POST'])
def edit_book():
    books = Book.query.all()
    authors = Author.query.all()
    publishers = Publisher.query.all()

    if request.method == 'POST':
        book_id = request.form['book_id']
        book = Book.query.get(book_id)
        book.title = request.form['title']
        book.author_id = request.form['author_id']
        book.publisher_id = request.form['publisher_id']
        book.publication_year = request.form['publication_year']
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_book.html', books=books, authors=authors, publishers=publishers)


@app.route('/books/delete', methods=['GET', 'POST'])
def delete_book():
    books = Book.query.all()

    if request.method == 'POST':
        book_id = request.form['book_id']
        book = Book.query.get(book_id)
        db.session.delete(book)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('delete_book.html', books=books)

@app.route('/borrow', methods=['GET', 'POST'])
def borrow_book():
    books = Book.query.all()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        book_id = request.form['book_id']

        # Check if borrower exists, if not, create a new one
        borrower = Borrower.query.filter_by(email=email).first()
        if not borrower:
            borrower = Borrower(first_name=first_name, last_name=last_name, email=email)
            db.session.add(borrower)
            db.session.commit()

        book = Book.query.get(book_id)
        if book.status == 'available':
            borrowed_date = date.today()
            due_date = borrowed_date + timedelta(days=14)  # Loan period is 14 days

            loan = Loan(book=book, borrower=borrower, borrowed_date=borrowed_date, due_date=due_date)
            book.status = 'borrowed'
            db.session.add(loan)
            db.session.commit()

            return redirect(url_for('list_books'))
        else:
            # Book is already borrowed
            return redirect(url_for('borrow_book'))

    return render_template('borrow_book.html', books=books)

@app.route('/books/list', methods=['GET'])
def list_books():
    status = request.args.get('status', 'all')
    status_label = 'All Books'

    if status == 'available':
        books = Book.query.filter(Book.status == 'available').all()
        status_label = 'Available Books'
    elif status == 'borrowed':
        books = Book.query.filter(Book.status == 'borrowed').all()
        status_label = 'Borrowed Books'
    else:
        books = Book.query.all()

    total_books = Book.query.count()
    borrowed_books = Book.query.filter(Book.status == 'borrowed').count()

    return render_template('list_books.html', books=books, status_label=status_label,
                           total_books=total_books, borrowed_books=borrowed_books)


@app.route('/return', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        loan_id = request.form['loan_id']
        loan = Loan.query.get(loan_id)
        if loan:
            loan.returned_date = date.today()
            loan.book.status = 'available'
            db.session.commit()
            return redirect(url_for('list_books'))
    
    loans = Loan.query.filter(Loan.returned_date == None).all()
    return render_template('return_book.html', loans=loans)



@app.route('/users', methods=['GET'])
def users():
    borrowers = Borrower.query.all()
    return render_template('users.html', borrowers=borrowers)

if __name__ == '__main__':
    app.run(debug=True)