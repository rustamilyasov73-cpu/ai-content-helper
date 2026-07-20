"""Тесты OCR-эвристик и матчинга по каталогу."""

from services.catalog import Catalog
from services.vision import (
    PhotoRecognition,
    extract_sku_candidates,
    match_recognition,
    _parse_vision_json,
)


def test_extract_sku_candidates():
    text = "Part No: RE507922  OEM AL156625  date 2024"
    found = extract_sku_candidates(text)
    assert "RE507922" in found
    assert "AL156625" in found


def test_extract_dotted_sku():
    found = extract_sku_candidates("код 0.012.4890.0 ROPA")
    assert found
    assert any(_compact_like(x) == "001248900" for x in found)


def _compact_like(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def test_parse_vision_json():
    raw = '{"raw_text":"FILTER RE507922","candidates":["RE507922"],"brand":"John Deere","model":"6R","notes":"бирка фильтра"}'
    result = _parse_vision_json(raw)
    assert result.candidates[0] == "RE507922"
    assert result.brand == "John Deere"


def test_match_recognition_to_catalog():
    catalog = Catalog()
    recognition = PhotoRecognition(
        raw_text="Oil filter RE-507922 John Deere",
        candidates=["RE-507922", "RE507922"],
        brand="John Deere",
    )
    matches = match_recognition(recognition, catalog)
    assert matches
    assert matches[0].sku == "RE507922"


def test_search_tolerates_ocr_noise():
    catalog = Catalog()
    # пробелы/дефисы как после OCR
    found = catalog.search("RE 507-922")
    assert found and found[0].sku == "RE507922"
