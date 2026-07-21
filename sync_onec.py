"""Синхронизация каталога AgroParts из 1С:Бухгалтерия.

Пример:
  python sync_onec.py
  python sync_onec.py --ping
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import BASE_DIR
from services.onec import is_configured, ping, sync_catalog

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("sync_onec")

MIRRORS = [
    BASE_DIR / "mobile" / "data" / "parts.json",
    BASE_DIR / "mobile" / "www" / "parts.json",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Синхронизация номенклатуры из 1С")
    parser.add_argument("--ping", action="store_true", help="Только проверить связь с 1С")
    args = parser.parse_args()

    if not is_configured():
        logger.error("Задайте ONEC_ENABLED=true и ONEC_BASE_URL в .env")
        return 1

    if args.ping:
        try:
            result = ping()
        except Exception as exc:
            logger.error("Ping failed: %s", exc)
            return 2
        logger.info("Ping OK: %s", result)
        return 0

    mirrors = [p for p in MIRRORS if p.parent.exists()]
    result = sync_catalog(mirror_paths=mirrors)
    if not result.ok:
        logger.error(result.message)
        return 3
    logger.info("%s → %s", result.message, result.path)
    for mirror in mirrors:
        logger.info("Зеркало: %s", mirror)
    return 0


if __name__ == "__main__":
    sys.exit(main())
