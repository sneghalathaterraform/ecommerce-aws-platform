import app as shop


def client():
    return shop.app.test_client()


def test_livez():
    r = client().get("/livez")
    assert r.status_code == 200
    assert r.get_json()["status"] == "alive"


def test_health_checks_database():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_products_are_seeded():
    r = client().get("/products")
    assert r.status_code == 200
    assert len(r.get_json()) >= 2


def test_create_and_list_order():
    c = client()
    r = c.post("/orders", json={"product_id": 1, "customer": "snegha"})
    assert r.status_code == 201
    orders = c.get("/orders").get_json()
    assert any(o["customer"] == "snegha" for o in orders)


def test_boom_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CHAOS_ENABLED", raising=False)
    assert client().get("/boom").status_code == 200


def test_boom_fails_when_chaos_enabled(monkeypatch):
    monkeypatch.setenv("CHAOS_ENABLED", "true")
    assert client().get("/boom").status_code == 500


def test_metrics_exposed():
    r = client().get("/metrics")
    assert r.status_code == 200
    assert b"shop_app_info" in r.data
