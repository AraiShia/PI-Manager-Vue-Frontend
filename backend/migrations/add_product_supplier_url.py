# -*- coding: utf-8 -*-
"""
迁移：添加 prd_product_supplier_url 表 + po_1688_purchase.supplier_id + 历史数据导入

修订历史：
  v5: 幂等保护（IF NOT EXISTS + column_exists）
  v6: PARTITION BY 增加 NULL 供应商按 supplier_name 分组；
      NOT EXISTS 双分支；downgrade out-of-scope
"""
import sqlalchemy as sa
from app.database import engine


def column_exists(conn, table: str, column: str) -> bool:
    """幂等保护——检查列是否存在"""
    rows = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def upgrade():
    with engine.begin() as conn:
        # 1. 新表（IF NOT EXISTS 幂等）
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS prd_product_supplier_url (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER,
                supplier_name VARCHAR(200) NOT NULL,
                url VARCHAR(500) NOT NULL,
                display_name VARCHAR(100),
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, supplier_id, url),
                FOREIGN KEY (product_id) REFERENCES prd_customer_product(id),
                FOREIGN KEY (supplier_id) REFERENCES sup_supplier(id)
            )
        """))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_psu_supplier ON prd_product_supplier_url(supplier_id)"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_psu_product ON prd_product_supplier_url(product_id)"))

        # 2. po_1688_purchase 新增 supplier_id（幂等：列存在时跳过）
        if not column_exists(conn, "po_1688_purchase", "supplier_id"):
            conn.execute(sa.text("""
                ALTER TABLE po_1688_purchase ADD COLUMN supplier_id INTEGER REFERENCES sup_supplier(id)
            """))

        # 3. 历史 supplier_id 回填（仅精确版本）
        conn.execute(sa.text("""
            UPDATE po_1688_purchase
            SET supplier_id = (
                SELECT id FROM sup_supplier
                WHERE sup_supplier.supplier_name = po_1688_purchase.supplier_name
                  AND sup_supplier.dept_id = po_1688_purchase.dept_id
                  AND sup_supplier.platform = '1688'
                LIMIT 1
            )
            WHERE supplier_id IS NULL
        """))

        # 4. 历史 URL 导入新表（v6: PARTITION BY 增加 NULL 供应商按 supplier_name 分组）
        # is_default = 1 当且仅当组内仅有一条记录（row_num_asc == row_num_desc == 1）
        # NOT EXISTS 双分支：supplier_id IS NOT NULL 时按 COALESCE 匹配；IS NULL 时按 supplier_name 匹配
        conn.execute(sa.text("""
            INSERT INTO prd_product_supplier_url
                (product_id, supplier_id, supplier_name, url, is_default, created_at)
            SELECT * FROM (
                SELECT
                    p.product_id,
                    p.supplier_id,
                    p.supplier_name,
                    p.product_url,
                    CASE WHEN p.row_num_asc = p.row_num_desc THEN 1 ELSE 0 END,
                    p.created_at
                FROM (
                    SELECT
                        p1.product_id,
                        p1.supplier_id,
                        p1.supplier_name,
                        p1.product_url,
                        p1.created_at,
                        p1.id,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                p1.product_id,
                                COALESCE(p1.supplier_id, 0),
                                CASE WHEN p1.supplier_id IS NULL THEN p1.supplier_name ELSE '' END,
                                p1.product_url
                            ORDER BY p1.created_at ASC, p1.id ASC
                        ) AS row_num_asc,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                p1.product_id,
                                COALESCE(p1.supplier_id, 0),
                                CASE WHEN p1.supplier_id IS NULL THEN p1.supplier_name ELSE '' END,
                                p1.product_url
                            ORDER BY p1.created_at DESC, p1.id DESC
                        ) AS row_num_desc
                    FROM po_1688_purchase p1
                    WHERE p1.product_url IS NOT NULL AND p1.product_url <> ''
                      AND p1.supplier_name IS NOT NULL AND p1.supplier_name <> ''
                ) p
                WHERE p.row_num_asc = 1
            ) p1
            WHERE NOT EXISTS (
                SELECT 1 FROM prd_product_supplier_url psu2
                WHERE psu2.product_id = p1.product_id
                  AND psu2.url = p1.product_url
                  AND (
                      (p1.supplier_id IS NOT NULL AND psu2.supplier_id IS NOT NULL
                       AND COALESCE(psu2.supplier_id, 0) = COALESCE(p1.supplier_id, 0))
                      OR
                      (p1.supplier_id IS NULL AND psu2.supplier_id IS NULL
                       AND psu2.supplier_name = p1.supplier_name)
                  )
            )
        """))

        # 5. 输出迁移统计
        total = conn.execute(sa.text("SELECT COUNT(*) FROM po_1688_purchase")).fetchone()[0]
        matched = conn.execute(sa.text("SELECT COUNT(*) FROM po_1688_purchase WHERE supplier_id IS NOT NULL")).fetchone()[0]
        unmatched = conn.execute(sa.text("SELECT COUNT(*) FROM po_1688_purchase WHERE supplier_id IS NULL")).fetchone()[0]
        imported = conn.execute(sa.text("SELECT COUNT(*) FROM prd_product_supplier_url")).fetchone()[0]
        print(f"[Migration] po_1688_purchase total={total}, supplier_id matched={matched}, unmatched={unmatched}")
        print(f"[Migration] prd_product_supplier_url imported={imported}")


def downgrade():
    # NOTE: downgrade 不在本次实现范围内
    # 如需回滚，请手动执行：
    # 1. DROP TABLE IF EXISTS prd_product_supplier_url;
    # 2. (可选) ALTER TABLE po_1688_purchase DROP COLUMN supplier_id;
    # 3. 人工确认无数据丢失
    raise NotImplementedError("Downgrade out of scope for this feature")


if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully.")
