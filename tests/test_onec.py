"""Тесты интеграции с 1С:Бухгалтерия."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from services import onec
from services.cart import Cart
from services.catalog import Catalog
from services.orders import save_order


def test_normalize_part_russian_fields():
    part = onec.normalize_part(
        {
            "Артикул": "RE507922",
            "Наименование": "Фильтр масляный",
            "Категория": "Фильтры",
            "Бренд": "John Deere",
            "Совместимость": "6R, 7R",
            "Цена": "2 890",
            "Остаток": 10,
            "Единица": "шт",
            "Описание": "тест",
        },
        index=1,
    )
    assert part["sku"] == "RE507922"
    assert part["category"] == "filters"
    assert part["price"] == 2890
    assert part["stock"] == 10
    assert part["compatible"] == ["6R", "7R"]


def test_build_order_payload():
    payload = onec.build_order_payload(
        phone="+70001112233",
        comment="6R",
        customer_name="Иван",
        source="test",
        external_id="ord-1",
        items=[{"sku": "RE507922", "name": "Фильтр", "qty": 2, "price": 100}],
    )
    assert payload["phone"] == "+70001112233"
    assert payload["total"] == 200
    assert payload["items"][0]["amount"] == 200


def test_push_order_skipped_when_disabled(monkeypatch):
    monkeypatch.setattr(onec, "ONEC_ENABLED", False)
    monkeypatch.setattr(onec, "ONEC_BASE_URL", "")
    result = onec.push_order(
        onec.build_order_payload(
            phone="+7000",
            items=[{"sku": "X", "name": "X", "qty": 1, "price": 1}],
        )
    )
    assert result.ok
    assert result.skipped


def test_push_order_http_ok(monkeypatch):
    monkeypatch.setattr(onec, "ONEC_ENABLED", True)
    monkeypatch.setattr(onec, "ONEC_BASE_URL", "http://1c.example/hs/agroparts")
    monkeypatch.setattr(onec, "ONEC_USER", "user")
    monkeypatch.setattr(onec, "ONEC_PASSWORD", "pass")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/orders")
        body = json.loads(request.content.decode("utf-8"))
        assert body["phone"] == "+70001112233"
        return httpx.Response(200, json={"ok": True, "number": "00042", "message": "ok"})

    transport = httpx.MockTransport(handler)

    class FakeClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(onec.httpx, "Client", FakeClient)
    result = onec.push_order(
        onec.build_order_payload(
            phone="+70001112233",
            items=[{"sku": "RE507922", "name": "Фильтр", "qty": 1, "price": 2890}],
        )
    )
    assert result.ok
    assert result.number == "00042"


def test_sync_catalog_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(onec, "ONEC_ENABLED", True)
    monkeypatch.setattr(onec, "ONEC_BASE_URL", "http://1c.example/hs/agroparts")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/nomenclature")
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "sku": "TEST-001",
                        "name": "Тест деталь",
                        "category": "filters",
                        "brand": "Test",
                        "price": 100,
                        "stock": 5,
                        "unit": "шт",
                        "description": "d",
                        "compatible": ["A"],
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    class FakeClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(onec.httpx, "Client", FakeClient)
    target = tmp_path / "parts.json"
    mirror = tmp_path / "mirror" / "parts.json"
    mirror.parent.mkdir()
    result = onec.sync_catalog(path=target, mirror_paths=[mirror])
    assert result.ok
    assert result.count == 1
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data[0]["sku"] == "TEST-001"
    assert mirror.exists()


def test_save_order_with_onec_disabled(tmp_path, monkeypatch):
    from services import orders as orders_mod

    monkeypatch.setattr(orders_mod, "ORDERS_DIR", tmp_path)
    monkeypatch.setattr(orders_mod, "ORDERS_FILE", tmp_path / "orders.jsonl")
    monkeypatch.setattr(onec, "ONEC_ENABLED", False)
    monkeypatch.setattr(onec, "ONEC_BASE_URL", "")

    catalog = Catalog()
    part = catalog.search("RE507922")[0]
    cart = Cart()
    cart.add(part, 1)
    path, record, onec_result = save_order(
        user_id=1,
        full_name="Test",
        username="t",
        cart=cart,
        note="note",
        phone="+70001112233",
    )
    assert path.exists()
    assert record["items"][0]["sku"] == "RE507922"
    assert onec_result is not None
    assert onec_result.skipped
