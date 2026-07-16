"""检查 pi_item 是否能保存 detail_desc_en / product_acquires / product_color。

运行方式（在 backend/ 目录）：
    python -m tests.check_pi_item_extra_fields
退出码：
    0 = 通过；1 = 字段缺失或 update 不生效。
"""
import importlib
import inspect
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


REQUIRED_MODEL_COLUMNS = {
    "detail_desc_en",
    "product_acquires",
    "product_color",
}

REQUIRED_UPDATE_FIELDS = {
    "detail_desc_en",
    "product_acquires",
    "product_color",
}

REQUIRED_READ_FIELDS = {
    "detail_desc_en",
    "product_acquires",
    "product_color",
}


def _missing(check_against: set, source_iterable) -> set:
    available = set()
    for name in source_iterable:
        if isinstance(name, str):
            available.add(name)
    return check_against - available


def main() -> int:
    failures = []

    model_module = importlib.import_module("models.pi")
    item_cls = model_module.PiProformaInvoiceItem
    model_columns = {col.key for col in item_cls.__table__.columns}
    missing_cols = _missing(REQUIRED_MODEL_COLUMNS, model_columns)
    if missing_cols:
        failures.append(("models/pi.py 缺少列", missing_cols))

    crud_module = importlib.import_module("crud.pi")
    update_fn = crud_module.update_pi_item
    src = inspect.getsource(update_fn)
    missing_update_fields = [
        field for field in REQUIRED_UPDATE_FIELDS if f"'{field}'" not in src
    ]
    if missing_update_fields:
        failures.append(("crud/pi.py update_pi_item 未处理字段", missing_update_fields))

    router_module = importlib.import_module("routers.pi")
    read_fn = router_module.read_pi_item
    src_read = inspect.getsource(read_fn)
    missing_read_fields = [
        field for field in REQUIRED_READ_FIELDS if field not in src_read
    ]
    if missing_read_fields:
        failures.append(("routers/pi.py read_pi_item 未返回字段", missing_read_fields))

    if failures:
        print("FAIL")
        for label, missing in failures:
            print(f"- {label}: {sorted(missing)}")
        return 1

    print("OK: model + update + read 都支持 detail_desc_en/product_acquires/product_color")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
