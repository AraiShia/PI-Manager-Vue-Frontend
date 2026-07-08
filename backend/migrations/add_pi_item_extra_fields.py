"""为 pi_proforma_invoice_item 补充:
- detail_desc_en (String 500) 产品英文名
- product_acquires (Text) 产品需求
- product_color (Text) 产品颜色

幂等：列已存在时跳过。
"""

import os
import sys

from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import engine


def upgrade():
    statements = [
        "ALTER TABLE pi_proforma_invoice_item ADD COLUMN detail_desc_en VARCHAR(500)",
        "ALTER TABLE pi_proforma_invoice_item ADD COLUMN product_acquires TEXT",
        "ALTER TABLE pi_proforma_invoice_item ADD COLUMN product_color TEXT",
    ]
    with engine.connect() as conn:
        for sql in statements:
            try:
                conn.execute(text(sql))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        conn.commit()


if __name__ == "__main__":
    upgrade()
