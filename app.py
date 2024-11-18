from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, User, Transaction ,Budget # Import your models
from auth import register_user, login_user, logout_user
from functools import wraps
from datetime import datetime, timedelta
from flask_login import current_user 
import shutil 

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'  # Ensure you have the right DB path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional, to suppress warning
db.init_app(app)

# Ensure tables are created before the first request
@app.before_request
def create_tables():
    db.create_all()

# Home route with login and registration
@app.route('/')
def home():
    return render_template('home.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password):
            flash('Registered successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists.', 'error')
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if login_user(username, password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    # Clear the session to log out the user
    session.clear()
    return redirect(url_for('login'))  

# Protect dashboard with login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Dashboard route with Financial Report button
@app.route('/dashboard')
@login_required
def dashboard():
    user = session['user']
    transactions = Transaction.query.filter_by(user=user).all()

    current_date = datetime.now()
    one_month_ago = current_date - timedelta(days=30)
    one_year_ago = current_date - timedelta(days=365)

    # Monthly report
    monthly_transactions = Transaction.query.filter(Transaction.user == user, Transaction.date >= one_month_ago).all()
    total_income_monthly = sum([t.amount for t in monthly_transactions if t.amount > 0])
    total_expenses_monthly = sum([t.amount for t in monthly_transactions if t.amount < 0])
    savings_monthly = total_income_monthly + total_expenses_monthly  # Expenses are negative

    # Yearly report
    yearly_transactions = Transaction.query.filter(Transaction.user == user, Transaction.date >= one_year_ago).all()
    total_income_yearly = sum([t.amount for t in yearly_transactions if t.amount > 0])
    total_expenses_yearly = sum([t.amount for t in yearly_transactions if t.amount < 0])
    savings_yearly = total_income_yearly + total_expenses_yearly  # Expenses are negative

    # User's profile info (Add logic to get user profile data)
    user_name = session['user']  # Example, you can replace with actual database query
    user_profile_picture_url = "/static/img/default_profile.png"  # Example, replace with actual profile picture URL

    return render_template('dashboard.html', 
                           transactions=transactions, 
                           total_income_monthly=total_income_monthly, 
                           total_expenses_monthly=total_expenses_monthly, 
                           savings_monthly=savings_monthly,
                           total_income_yearly=total_income_yearly, 
                           total_expenses_yearly=total_expenses_yearly, 
                           savings_yearly=savings_yearly,
                           user_name=user_name,
                           user_profile_picture_url=user_profile_picture_url)

# Add transaction route
@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        user = session['user']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')  # Parse date
        new_transaction = Transaction(user=user, amount=amount, category=category, date=date)
        db.session.add(new_transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_transaction.html')

# Edit transaction route
@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if request.method == 'POST':
        transaction.amount = float(request.form['amount'])
        transaction.category = request.form['category']
        transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')  # Parse new date
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_transaction.html', transaction=transaction)

# Delete transaction route
@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/report', methods=['GET', 'POST'])
def report():
    # Get the selected month from the form (defaults to current month if no selection)
    selected_month = request.form.get('month', default=datetime.now().month, type=int)

    # Month names for reference
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    # Get the selected month name
    selected_month_name = month_names[selected_month - 1]

    # Financial data for the selected month (you can replace these with real data queries)
    total_income_monthly = 3000  # Example static data, replace with your calculation logic
    total_expenses_monthly = 1500
    savings_monthly = total_income_monthly - total_expenses_monthly

    # Yearly data (replace with real data calculation logic)
    total_income_yearly = 36000
    total_expenses_yearly = 18000
    savings_yearly = total_income_yearly - total_expenses_yearly

    # Pass variables to the template
    return render_template(
        'report.html',
        selected_month=selected_month,
        selected_month_name=selected_month_name,
        total_income_monthly=total_income_monthly,
        total_expenses_monthly=total_expenses_monthly,
        savings_monthly=savings_monthly,
        total_income_yearly=total_income_yearly,
        total_expenses_yearly=total_expenses_yearly,
        savings_yearly=savings_yearly
    )
@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        budget = Budget(user_id=current_user.id, category=category, amount=amount)
        db.session.add(budget)
        db.session.commit()
        flash('Budget set successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('set_budget.html')

@app.route('/backup', methods=['POST'])
def backup():
    try:
        shutil.copy('finance_app.db', 'backups/finance_app_backup.db')
        flash('Backup created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating backup: {e}', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/restore', methods=['POST'])
def restore():
    try:
        shutil.copy('backups/finance_app_backup.db', 'finance_app.db')
        flash('Data restored successfully!', 'success')
    except Exception as e:
        flash(f'Error restoring data: {e}', 'danger')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
