from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    address = db.Column(db.String(255))
    postcode = db.Column(db.String(20))
    service = db.Column(db.String(120))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_email = db.Column(db.String(256), index=True)
    subject = db.Column(db.Text)
    body = db.Column(db.Text)
    from_addr = db.Column(db.String(256))
    to_addr = db.Column(db.String(256))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    folder = db.Column(db.String(64))
    msgid = db.Column(db.String(256), unique=True, index=True)