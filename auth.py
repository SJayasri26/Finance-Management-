from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password):
    if User.query.filter_by(username=username).first():
        return False
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return True

def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return True
    return False

def logout_user():
    session.pop('user', None)
