"""Юнит-тесты каталога, корзины и заявок AgroParts."""

import json
from pathlib import Path

from services.cart import Cart
from services.catalog import Catalog, load_parts
from services.orders import save_order


def test_load_parts():
    parts = load_parts()
    assert len(parts) >= 10
    assert parts[0].sku


def test_search_by_sku():
    catalog = Catalog()
    found = catalog.search("RE507922")
    assert len(found) == 1
    assert found[0].name.startswith("Фильтр масляный")


def test_search_by_brand_and_name():
    catalog = Catalog()
    found = catalog.search("фильтр John Deere")
    assert found
    assert any("John Deere" in p.brand for p in found)


def test_categories_and_brands():
    catalog = Catalog()
    cats = catalog.categories()
    brands = catalog.brands()
    assert cats
    assert brands
    assert any(key == "filters" for key, _, _ in cats)
    john = catalog.by_brand("John Deere")
    assert john


def test_reload_catalog():
    catalog = Catalog()
    n1 = len(catalog.all())
    n2 = catalog.reload()
    assert n1 == n2


def test_cart_qty_and_stock_cap():
    catalog = Catalog()
    part = catalog.search("RE507922")[0]
    cart = Cart()
    cart.add(part, 2)
    assert cart.total_qty() == 2
    cart.change(part.id, 1)
    assert cart.items[part.id].qty == 3
    cart.set_qty(part.id, part.stock + 100)
    assert cart.items[part.id].qty == part.stock
    cart.change(part.id, -1000)
    assert cart.is_empty()


def test_save_order(tmp_path, monkeypatch):
    from services import orders as orders_mod

    monkeypatch.setattr(orders_mod, "ORDERS_DIR", tmp_path)
    monkeypatch.setattr(orders_mod, "ORDERS_FILE", tmp_path / "orders.jsonl")

    catalog = Catalog()
    part = catalog.search("RE507922")[0]
    cart = Cart()
    cart.add(part, 1)
    path = save_order(
        user_id=1,
        full_name="Test User",
        username="tester",
        cart=cart,
        note="трактор 6R",
        phone="+70001112233",
    )
    assert path.exists()
    row = json.loads(Path(path).read_text(encoding="utf-8").strip())
    assert row["total_qty"] == 1
    assert row["phone"] == "+70001112233"
    assert row["items"][0]["sku"] == "RE507922"
