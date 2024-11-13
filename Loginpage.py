import sqlite3
from getpass import getpass
import hashlib
import csv

# Database setup
conn = sqlite3.connect('finance_manager.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
             id INTEGER PRIMARY KEY,
             username TEXT,
             type TEXT,
             category TEXT,
             amount REAL,
             date TEXT)''')
conn.commit()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def register():
    """Register a new user."""
    username = input("Enter a unique username: ")
    password = getpass("Enter a password: ")
    hashed_password = hash_password(password)
    
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print("User registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already taken. Please choose a different username.")

def login():
    """Authenticate an existing user."""
    username = input("Enter your username: ")
    password = getpass("Enter your password: ")
    hashed_password = hash_password(password)
    
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    if c.fetchone():
        print("Login successful!")
        return username
    else:
        print("Login failed! Please check your username and password.")
        return None

def add_transaction(username, type, category, amount, date):
    c.execute("INSERT INTO transactions (username, type, category, amount, date) VALUES (?, ?, ?, ?, ?)", (username, type, category, amount, date))
    conn.commit()
    print(f"{type.capitalize()} added successfully!")

def update_transaction(transaction_id, type, category, amount, date):
    c.execute("UPDATE transactions SET type=?, category=?, amount=?, date=? WHERE id=?", (type, category, amount, date, transaction_id))
    conn.commit()
    print("Transaction updated successfully!")

def delete_transaction(transaction_id):
    c.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
    conn.commit()
    print("Transaction deleted successfully!")

def view_transactions(username):
    c.execute("SELECT * FROM transactions WHERE username=?", (username,))
    rows = c.fetchall()
    for row in rows:
        print(row)

def generate_report(username, period):
    if period == 'monthly':
        c.execute("SELECT type, SUM(amount) FROM transactions WHERE username=? GROUP BY strftime('%Y-%m', date)", (username,))
    else:
        c.execute("SELECT type, SUM(amount) FROM transactions WHERE username=? GROUP BY strftime('%Y', date)", (username,))
    rows = c.fetchall()
    for row in rows:
        print(f"Type: {row[0]}, Total: {row[1]}")

def set_budget(username, category, budget):
    c.execute("INSERT INTO budgets (username, category, budget) VALUES (?, ?, ?)", (username, category, budget))
    conn.commit()
    print("Budget set successfully!")

def check_budget(username, category):
    c.execute("SELECT budget FROM budgets WHERE username=? AND category=?", (username, category))
    budget = c.fetchone()
    if budget:
        c.execute("SELECT SUM(amount) FROM transactions WHERE username=? AND category=?", (username, category))
        total_spent = c.fetchone()[0]
        if total_spent and total_spent > budget[0]:
            print(f"Alert: You have exceeded your budget for {category}!")

def backup_data():
    with open('backup.sql', 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    print("Data backed up successfully!")

def restore_data():
    with open('backup.sql', 'r') as f:
        sql = f.read()
        conn.executescript(sql)
    print("Data restored successfully!")

def save_to_csv(username):
    c.execute("SELECT * FROM transactions WHERE username=?", (username,))
    rows = c.fetchall()
    with open(f'{username}_transactions.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Username', 'Type', 'Category', 'Amount', 'Date'])
        writer.writerows(rows)
    print(f"Transactions saved to {username}_transactions.csv")

def load_from_csv(username):
    with open(f'{username}_transactions.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            c.execute("INSERT INTO transactions (id, username, type, category, amount, date) VALUES (?, ?, ?, ?, ?, ?)", row)
        conn.commit()
    print(f"Transactions loaded from {username}_transactions.csv")

def main():
    """Main loop for user interaction."""
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = int(input("Enter your choice: "))
        
        if choice == 1:
            register()
        elif choice == 2:
            username = login()
            if username:
                print("Welcome to the Personal Finance Management Application!")
                user_menu(username)
        elif choice == 3:
            break
        else:
            print("Invalid choice! Please choose again.")

def user_menu(username):
    while True:
        print("\n1. Add Transaction\n2. View Transactions\n3. Set Budget\n4. Check Budget\n5. Generate Report\n6. Save to CSV\n7. Load from CSV\n8. Logout")
        choice = int(input("Enter your choice: "))
        
        if choice == 1:
            type = input("Enter transaction type (income/expense): ")
            category = input("Enter transaction category (e.g., Salary, Food): ")
            amount = float(input("Enter amount: "))
            date = input("Enter date (YYYY-MM-DD): ")
            add_transaction(username, type, category, amount, date)
        elif choice == 2:
            view_transactions(username)
        elif choice == 3:
            category = input("Enter category: ")
            budget = float(input("Enter budget amount: "))
            set_budget(username, category, budget)
        elif choice == 4:
            category = input("Enter category: ")
            check_budget(username, category)
        elif choice == 5:
            period = input("Enter report period (monthly/yearly): ")
            generate_report(username, period)
        elif choice == 6:
            save_to_csv(username)
        elif choice == 7:
            load_from_csv(username)
        elif choice == 8:
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
