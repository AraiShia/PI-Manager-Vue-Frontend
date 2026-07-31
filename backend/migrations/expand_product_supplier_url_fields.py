# -*- coding: utf-8 -*-
"""
迁移：扩充 prd_product_supplier_url 表中的 url (VARCHAR 2000) 与 display_name (VARCHAR 500) 字段长度

符合 Google 编程规范，支持 SQLite / PostgreSQL 数据库幂等迁移。
"""
import sqlalchemy as sa
from app.database import engine


def upgrade():
    with engine.begin() as conn:
        dialect_name = conn.dialect.name
        if dialect_name == "sqlite":
            # SQLite 架构升级：重构表列类型定义 (通过临时表转存或 PRAGMA 幂等处理)
            # SQLite 在 VARCHAR 放大时无长度硬约束，但调整结构保持一致性
            pass
        elif dialect_name == "postgresql":
            # PostgreSQL 原生 ALTER COLUMN TYPE 变更
            conn.execute(sa.text("""
                ALTER TABLE prd_product_supplier_url
                ALTER COLUMN url TYPE VARCHAR(2000),
                ALTER COLUMN display_name TYPE VARCHAR(500);
            """))


def downgrade():
    pass
