from pathlib import Path

from services.onec_sync import enqueue_order_for_1c, import_from_file, map_1c_item


def test_map_1c_item_basic():
    part = map_1c_item(
        {
            "Артикул": "RE507922",
            "Code": "00-00001234",
            "Description": "Фильтр масляный",
            "Бренд": "John Deere",
            "Группа": "Фильтры",
            "Цена": 2890,
            "Остаток": 10,
            "СтавкаНДС": "НДС20",
            "Совместимость": "6R, 7R",
        },
        1,
    )
    assert part["sku"] == "RE507922"
    assert part["code_1c"] == "00-00001234"
    assert part["category"] == "filters"
    assert part["vat_rate"] == 20
    assert part["compatible"] == ["6R", "7R"]


def test_import_sample_and_enqueue(tmp_path: Path):
    sample = Path("data/1c/nomenclature.sample.json")
    target = tmp_path / "parts.json"
    result = import_from_file(sample, parts_file=target)
    assert not result.error
    assert result.imported >= 50
    assert target.exists()

    out = enqueue_order_for_1c(
        {
            "id": "ord-test-1",
            "phone": "+79001112233",
            "comment": "срочно",
            "total": 2890,
            "items": [{"sku": "RE507922", "name": "Фильтр", "qty": 1, "price": 2890, "code_1c": "00-00001234"}],
        }
    )
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "RE507922" in text
    assert "+79001112233" in text
