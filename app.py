from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
from models import db, User, Expense

app = Flask(__name__)

# -------------------------------
# CONFIGURATION
# -------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

db.init_app(app)

# -------------------------------
# SIGNUP ROUTE
# -------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------------------------------
# LOGIN ROUTE
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

# -------------------------------
# LOGOUT ROUTE
# -------------------------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------
# MAIN DASHBOARD
# -------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    categories = {}
    for e in expenses:
        categories.setdefault(e.category, 0)
        categories[e.category] += e.amount

    return render_template('index.html', expenses=expenses, total=total, categories=categories)

# -------------------------------
# ADD EXPENSE
# -------------------------------
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            date_str = request.form['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            category = request.form['category'].strip()
            amount = float(request.form['amount'])
            description = request.form.get('description', '').strip()

            new_expense = Expense(
                date=date_obj,
                category=category,
                amount=amount,
                description=description,
                user_id=session['user_id']
            )
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding expense: ' + str(e), 'danger')

    return render_template('add.html')

# -------------------------------
# EDIT EXPENSE
# -------------------------------
@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    exp = Expense.query.get_or_404(expense_id)

    if request.method == 'POST':
        try:
            exp.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            exp.category = request.form['category'].strip()
            exp.amount = float(request.form['amount'])
            exp.description = request.form.get('description', '').strip()
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating expense: ' + str(e), 'danger')

    return render_template('edit.html', expense=exp)

# -------------------------------
# DELETE EXPENSE
# -------------------------------
@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    exp = Expense.query.get_or_404(expense_id)
    try:
        db.session.delete(exp)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting expense: ' + str(e), 'danger')
    return redirect(url_for('index'))

# -------------------------------
# RUN THE APP
# -------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
