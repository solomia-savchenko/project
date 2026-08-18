import datetime
import secrets
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user
from models import Order, Pizza, User, db

app = Flask(__name__)

# Flask config
app.config["SECRET_KEY"] = "]'/[;.[__-]]"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:ostap2301@localhost:5432/pizzeria"

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
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' https://cdn.jsdelivr.net; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    response.set_cookie("nonce", nonce)
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

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)  # Виправлено помилку: авторизуємо новоствореного new_user
        return redirect(url_for("home"))

    return render_template("register.html")

def create_positions():
    if not Pizza.query.first():
        margherita = Pizza(name="Margherita", description="Classic mozzarella and tomato sauce", price=180)
        pepperoni = Pizza(name="Pepperoni", description="Spicy pepperoni sausage with cheese", price=230)
        four_cheeses = Pizza(name="Four Cheeses", description="Mozzarella, gorgonzola, parmesan, and cheddar", price=260)

        db.session.add_all([margherita, pepperoni, four_cheeses])
        db.session.commit()

@app.route("/menu")
def menu():
    all_positions = Pizza.query.filter_by(is_active=True).all()
    return render_template("menu.html", all_positions=all_positions)

@app.route("/bucket")
def bucket():
    bucket = session.get("bucket", {})
    return bucket

@app.route("/position/<name>", methods=["GET", "POST"])
def position(name):
    if request.method == "POST":
        if request.form.get("csrf_token") != session.get("csrf_token"):
            return "Request blocked", 403

        ammount = request.form.get("ammount")

        bucket = session.get("bucket", {})
        bucket[name] = ammount
        session["bucket"] = bucket

        return redirect(url_for("menu"))

    position = Pizza.query.filter_by(name=name).first()
    return render_template("position.html", csrf_token=session["csrf_token"], position=position)

@app.route("/order", methods=["GET", "POST"])
@login_required
def order():
    bucket = session.get("bucket")
    if request.method == "POST":
        if request.form.get("csrf_token") != session.get("csrf_token"):
            return "Request blocked", 403

        if not bucket:
            return "Bucket is empty"

        new_order = Order(order_list=bucket, order_time=datetime.datetime.now(), user_id=current_user.id)
        db.session.add(new_order)
        db.session.commit()
        session.pop("bucket", None)
        return redirect(url_for("home"))

    return render_template("order.html", bucket=bucket, csrf_token=session["csrf_token"])

@app.route("/admin_orders", methods=["GET","POST"])
@login_required
def admin_orders():
    if not current_user.username == "admin":
        return "помилка тільки для адмінів!"
    all_orders = Order.query.filter_by(status=False).all()
    if not all_orders:
        return "немає замовлень"
    if request.method == "POST":
        if request.form.get("csrf_token") != session.get("csrf_token"):
            return "Request blocked", 403
        order_id = request.form.get("order_id")
        current_order = Order.query.filter_by(id=order_id).first()
        current_order.status = True

        db.session.commit()
        return redirect(url_for("home"))
    return render_template("admin_orders.html", all_orders=all_orders, csrf_token=session["csrf_token"])

@app.route("/my_orders")
@login_required
def my_orders():
    my_orders = Order.query.filter_by(status=False, user_id=current_user.id).all()
    if not my_orders:
        return "немає замовлень"
    return render_template("my_orders.html", my_orders=my_orders)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_positions()
    app.run(debug=True)