"""为 pi_proforma_invoice_item 添加产品简称字段"""

import os
import sys

from sqlalchemy import text


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import engine


def upgrade():
    statements = [
        "ALTER TABLE pi_proforma_invoice_item ADD COLUMN product_short_name VARCHAR(200)",
        "ALTER TABLE pi_proforma_invoice_item ADD COLUMN product_short_name_en VARCHAR(200)",
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
