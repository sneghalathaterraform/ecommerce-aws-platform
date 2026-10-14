import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite://")
db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)  # adds /metrics
metrics.info("shop_app_info", "Application info", version=os.environ.get("APP_VERSION", "dev"))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    customer = db.Column(db.String(100), nullable=False)


@app.get("/livez")  # liveness: process is up, no database call
def livez():
    return jsonify(status="alive")


@app.get("/health")  # readiness: database must answer
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok")
    except Exception:
        return jsonify(status="error"), 503


@app.get("/products")
def products():
    return jsonify([{"id": p.id, "name": p.name, "price": p.price} for p in Product.query.all()])


@app.route("/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        data = request.get_json()
        db.session.add(Order(product_id=data["product_id"], customer=data["customer"]))
        db.session.commit()
        return jsonify(status="created"), 201
    return jsonify([{"id": o.id, "product_id": o.product_id, "customer": o.customer} for o in Order.query.all()])


@app.get("/boom")  # failure drill: 500 only when CHAOS_ENABLED=true
def boom():
    if os.environ.get("CHAOS_ENABLED") == "true":
        return jsonify(error="simulated failure"), 500
    return jsonify(status="chaos disabled")


with app.app_context():
    db.create_all()
    if not Product.query.first():
        db.session.add_all([Product(name="Laptop", price=55000), Product(name="Keyboard", price=1500)])
        db.session.commit()
