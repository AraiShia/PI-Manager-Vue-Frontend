"""为 PI 商品项增加可独立编辑的贴标费字段。"""

from sqlalchemy import text

from app.database import engine


def upgrade():
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE pi_proforma_invoice_item "
                "ADD COLUMN labeling_fee DECIMAL(15, 4)"
            ))
        except Exception as exc:
            if "duplicate column name" not in str(exc).lower():
                raise
        conn.commit()


if __name__ == "__main__":
    upgrade()
