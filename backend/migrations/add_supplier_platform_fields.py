"""为 sup_supplier 和 po_purchase_order 增加平台分类字段。

执行：docker compose exec backend python -m migrations.add_supplier_platform_fields
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    with engine.connect() as conn:
        # ── 1. sup_supplier 新增字段 ────────────────────────────────
        for ddl in [
            "ALTER TABLE sup_supplier ADD COLUMN platform VARCHAR(20)",
            "ALTER TABLE sup_supplier ADD COLUMN shop_link VARCHAR(500)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_id VARCHAR(100)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_nickname VARCHAR(100)",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        try:
            conn.execute(text(
                "ALTER TABLE sup_supplier ADD COLUMN is_dropship BOOLEAN NOT NULL DEFAULT 0"
            ))
        except Exception as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

        # ── 2. po_purchase_order 新增字段 ─────────────────────────
        for ddl in [
            "ALTER TABLE po_purchase_order ADD COLUMN platform VARCHAR(20)",
            "ALTER TABLE po_purchase_order ADD COLUMN shop_link VARCHAR(500)",
            "ALTER TABLE po_purchase_order ADD COLUMN wechat_id VARCHAR(100)",
            "ALTER TABLE po_purchase_order ADD COLUMN wechat_nickname VARCHAR(100)",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        try:
            conn.execute(text(
                "ALTER TABLE po_purchase_order ADD COLUMN is_dropship BOOLEAN NOT NULL DEFAULT 0"
            ))
        except Exception as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

        # ── 3. 检查 sup_supplier 重复数据（创建唯一索引前诊断） ───
        duplicate_rows = conn.execute(text("""
            SELECT dept_id, platform, supplier_name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
            FROM sup_supplier
            WHERE dept_id IS NOT NULL
              AND platform IS NOT NULL
              AND supplier_name IS NOT NULL
              AND supplier_name != ''
            GROUP BY dept_id, platform, supplier_name
            HAVING COUNT(*) > 1
        """)).fetchall()

        if duplicate_rows:
            lines = "\n".join(
                f"  dept_id={r[0]}, platform={r[1]}, supplier_name={r[2]}, "
                f"重复数量={r[3]}, ids={r[4]}"
                for r in duplicate_rows
            )
            raise RuntimeError(
                f"发现 {len(duplicate_rows)} 组重复供应商数据，请先在数据库中合并或删除重复记录后再执行迁移。\n{lines}"
            )

        # ── 4. 创建唯一索引（NULL 不参与约束） ─────────────────────
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX uq_supplier_dept_platform_name "
                "ON sup_supplier(dept_id, platform, supplier_name)"
            ))
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                raise

        conn.commit()
        print("OK: sup_supplier + po_purchase_order platform 字段迁移完成")


if __name__ == "__main__":
    upgrade()
