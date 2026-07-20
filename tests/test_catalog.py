"""Юнит-тесты каталога и корзины AgroParts."""

from services.cart import Cart
from services.catalog import Catalog, load_parts


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


def test_categories():
    catalog = Catalog()
    cats = catalog.categories()
    assert cats
    assert any(key == "filters" for key, _, _ in cats)


def test_cart_total():
    catalog = Catalog()
    part = catalog.search("RE507922")[0]
    cart = Cart()
    cart.add(part, 2)
    assert cart.total_qty() == 2
    assert cart.total_price() == part.price * 2
    cart.clear()
    assert cart.is_empty()
