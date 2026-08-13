import secrets

from flask import Flask, redirect, render_template, request, url_for, session
from flask_login import LoginManager, login_required, current_user, login_user
from models import Kebab, Order, db, User
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)

# Flask config
app.config["SECRET_KEY"] = "]'/[;.[__-]]"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:dima2902@localhost:5432/restauraunt'

db.init_app(app)

# Login manager config
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.after_request
def apply_csp(response):
    nonce = secrets.token_urlsafe(16)
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    response.set_cookie('nonce', nonce)
    return response

@app.before_request
def ensure_csrf_token():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/")
def home():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return render_template("home.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            return "Wrong username or password"
    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            return "User exists"

        new_user = User(username=username, password=password)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("home"))

    return render_template("register.html")

def create_positions():
    if not Kebab.query.first():
        small = Kebab(name="Small Kebab", description="a little one for kids", price=120)
        medium = Kebab(name="Medium Kebab", description="medium is classic", price=180)
        big = Kebab(name="Big boss", description="double meat", price=200)

        db.session.add_all([small, medium, big])
        db.session.commit()

@app.route("/menu")
def menu():
    all_positions = Kebab.query.filter_by(is_active=True).all()
    return render_template("menu.html", all_positions=all_positions)

@app.route("/bucket")
def bucket():
    bucket = session.get("bucket", {})
    return bucket

@app.route("/position/<name>", methods=["GET", "POST"])
def position(name):
    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Request blocked", 403

        ammount = request.form.get("ammount")

        if "bucket" not in session:
            bucket = {}
            bucket[name] = ammount
            session["bucket"] = bucket
        else:
            bucket = session.get("bucket")
            bucket[name] = ammount
            session["bucket"] = bucket

        return redirect(url_for("menu"))

    position = Kebab.query.filter_by(name=name).first()
    return render_template("position.html", csrf_token=session["csrf_token"], position=position)

@login_required
@app.route("/order", methods=["GET", "POST"])
def order():
    bucket = session.get("bucket")
    if request.method == "POST":
        if request.form.get("csrf_token") != session["csrf_token"]:
            return "Request blocked", 403

        if not bucket:
            return "Bucket is empty"

        new_order = Order(order_list=bucket, order_time=datetime.datetime.now(), user_id=current_user.id)
        db.session.add(new_order)
        db.session.commit()
        session.pop("bucket")
        return redirect(url_for("home"))

    return render_template("order.html", bucket=bucket, csrf_token=session["csrf_token"])

if __name__=="__main__":
    with app.app_context():
        db.create_all()
        create_positions()
    app.run(debug=True)