import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password, method='pbkdf2:sha256')

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

class Pizza(db.Model):
    __tablename__ = "pizzas"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_list = db.Column(db.JSON, nullable=False)
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="orders")