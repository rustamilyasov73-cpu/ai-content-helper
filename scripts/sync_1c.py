#!/usr/bin/env python3
"""CLI синхронизации с 1С.

Примеры:
  python scripts/sync_1c.py import-file data/1c/nomenclature.sample.json
  python scripts/sync_1c.py import-http https://1c.example/hs/agroparts/nomenclature --token SECRET
  python scripts/sync_1c.py export-orders
  python scripts/sync_1c.py push-orders https://1c.example/hs/agroparts/orders --token SECRET
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.onec_sync import (  # noqa: E402
    export_pending_orders,
    import_from_file,
    import_from_http,
    push_order_http,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="AgroParts ↔ 1С обмен")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_file = sub.add_parser("import-file", help="Импорт номенклатуры из JSON файла 1С")
    p_file.add_argument("path", type=Path)

    p_http = sub.add_parser("import-http", help="Импорт номенклатуры по HTTP из 1С")
    p_http.add_argument("url")
    p_http.add_argument("--token", default="")

    sub.add_parser("export-orders", help="Показать заявки в outbox для 1С")

    p_push = sub.add_parser("push-orders", help="Отправить outbox-заявки в HTTP-сервис 1С")
    p_push.add_argument("url")
    p_push.add_argument("--token", default="")

    args = parser.parse_args()

    if args.cmd == "import-file":
        result = import_from_file(args.path)
        if result.error:
            print("ERROR:", result.error)
            return 1
        print(f"OK imported={result.imported} source={result.source}")
        return 0

    if args.cmd == "import-http":
        result = import_from_http(args.url, token=args.token)
        if result.error:
            print("ERROR:", result.error)
            return 1
        print(f"OK imported={result.imported} source={result.source}")
        return 0

    if args.cmd == "export-orders":
        files = export_pending_orders()
        print(f"pending={len(files)}")
        for path in files:
            print(path)
        return 0

    if args.cmd == "push-orders":
        files = export_pending_orders()
        ok_n = 0
        for path in files:
            try:
                if push_order_http(path, args.url, token=args.token):
                    ok_n += 1
                    print("sent", path.name)
            except Exception as exc:  # noqa: BLE001
                print("fail", path.name, exc)
        print(f"OK sent={ok_n}/{len(files)}")
        return 0 if ok_n == len(files) else 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
