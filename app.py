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


# ---- Simple web UI ----
from flask import render_template_string, redirect

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ecommerce</title>
<style>
  :root{--ink:#1f2937;--muted:#6b7280;--bg:#f3f4fb;--card:#ffffff;--line:#e5e7f0;
        --c1:#6366f1;--c2:#14b8a6;--c3:#f59e0b;--c4:#ec4899}
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
  header{background:linear-gradient(120deg,#4f46e5,#7c3aed 55%,#ec4899);color:#fff;padding:22px 24px}
  .bar{max-width:1000px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
  .brand{display:flex;align-items:center;gap:12px}
  .logo{width:42px;height:42px;border-radius:12px;background:rgba(255,255,255,.2);display:grid;place-items:center;font-weight:700;font-size:20px}
  .brand h1{margin:0;font-size:22px}
  .brand small{opacity:.85}
  .pill{background:rgba(255,255,255,.2);border-radius:999px;padding:5px 12px;font-size:13px}
  main{max-width:1000px;margin:-18px auto 32px;padding:0 16px}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:22px}
  .stat{background:var(--card);border-radius:14px;padding:16px 18px;box-shadow:0 4px 14px rgba(79,70,229,.10);border-top:4px solid var(--c1)}
  .stat:nth-child(2){border-color:var(--c2)} .stat:nth-child(3){border-color:var(--c3)} .stat:nth-child(4){border-color:var(--c4)}
  .stat .n{font-size:26px;font-weight:700} .stat .l{color:var(--muted);font-size:13px}
  h2{margin:0 0 14px;font-size:17px}
  .panel{background:var(--card);border-radius:14px;padding:18px 20px;box-shadow:0 4px 14px rgba(79,70,229,.08);margin-bottom:22px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}
  .product{border:1px solid var(--line);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px}
  .icon{width:46px;height:46px;border-radius:12px;color:#fff;display:grid;place-items:center;font-size:20px;font-weight:700}
  .k1 .icon{background:var(--c1)} .k2 .icon{background:var(--c2)} .k3 .icon{background:var(--c3)} .k0 .icon{background:var(--c4)}
  .product .name{font-weight:600;font-size:16px}
  .product .price{font-size:20px;font-weight:700}
  .btn{display:inline-block;text-align:center;text-decoration:none;border:0;cursor:pointer;color:#fff;background:var(--c1);
       padding:9px 14px;border-radius:8px;font-size:14px;font-weight:600}
  .k2 .btn{background:var(--c2)} .k3 .btn{background:var(--c3)} .k0 .btn{background:var(--c4)}
  .cols{display:grid;grid-template-columns:1fr 1.4fr;gap:22px}
  @media(max-width:760px){.cols{grid-template-columns:1fr}}
  form{display:flex;flex-direction:column;gap:10px}
  label{font-size:13px;color:var(--muted)}
  select,input{padding:10px 12px;font-size:15px;border:1px solid var(--line);border-radius:8px;background:#fff}
  table{width:100%;border-collapse:collapse}
  th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);text-align:left;padding:8px 10px}
  td{padding:10px;border-top:1px solid var(--line)}
  .chip{background:#eef2ff;color:#4338ca;border-radius:999px;padding:3px 10px;font-size:13px}
  .empty{color:var(--muted)}
  footer{text-align:center;color:var(--muted);font-size:13px;padding:0 16px 28px}
</style></head><body>
<header><div class="bar">
  <div class="brand"><div class="logo">E</div><div><h1>Ecommerce</h1></div></div>
</div></header>
<main>
  <div class="stats">
    <div class="stat"><div class="n">{{ products|length }}</div><div class="l">Products</div></div>
    <div class="stat"><div class="n">{{ orders|length }}</div><div class="l">Orders</div></div>
  </div>

  <div class="panel">
    <h2>Products</h2>
    <div class="grid">
      {% for p in products %}
      <div class="product k{{ loop.index % 4 }}">
        <div class="icon">{{ p.name[0] }}</div>
        <div class="name">{{ p.name }}</div>
        <div class="price">&#8377; {{ '{:,.0f}'.format(p.price) }}</div>
        <a class="btn" href="/?pick={{ p.id }}#order">Order this</a>
      </div>
      {% endfor %}
    </div>
  </div>

  <div class="cols">
    <div class="panel" id="order">
      <h2>Place an order</h2>
      <form method="post" action="/place-order">
        <label>Product</label>
        <select name="product_id">
          {% for p in products %}<option value="{{ p.id }}" {% if p.id|string == pick %}selected{% endif %}>{{ p.name }}</option>{% endfor %}
        </select>
        <label>Customer name</label>
        <input name="customer" placeholder="e.g. Snegha" required>
        <button class="btn" type="submit">Place order</button>
      </form>
    </div>
    <div class="panel">
      <h2>Orders</h2>
      {% if orders %}
      <table>
        <tr><th>Order</th><th>Product</th><th>Customer</th></tr>
        {% for o in orders %}
        <tr><td>#{{ o.id }}</td><td><span class="chip">{{ names.get(o.product_id, o.product_id) }}</span></td><td>{{ o.customer }}</td></tr>
        {% endfor %}
      </table>
      {% else %}<p class="empty">No orders yet. Place the first one.</p>{% endif %}
    </div>
  </div>
</main>
<footer>Flask &middot; PostgreSQL &middot; Docker &middot; Kubernetes (EKS) &middot; Helm &middot; ArgoCD &middot; Prometheus &middot; Grafana</footer>
</body></html>"""


@app.get("/")
def home():
    products = Product.query.order_by(Product.id).all()
    orders = Order.query.order_by(Order.id.desc()).all()
    names = {p.id: p.name for p in products}
    return render_template_string(PAGE, products=products, orders=orders, names=names,
                                  pick=request.args.get("pick", ""),
                                  version=os.environ.get("APP_VERSION", "dev"),
                                  pod=os.environ.get("HOSTNAME", "local"))


@app.post("/place-order")
def place_order():
    db.session.add(Order(product_id=int(request.form["product_id"]),
                         customer=request.form["customer"].strip() or "guest"))
    db.session.commit()
    return redirect("/")
