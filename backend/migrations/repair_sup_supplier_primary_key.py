# -*- coding: utf-8 -*-
"""修复 sup_supplier 缺失 INTEGER PRIMARY KEY 的历史数据库。

历史数据库中的 ``id`` 被创建成普通 INT，SQLite 实际使用隐藏的 rowid，
导致 SQLAlchemy 在插入后得到的主键无法通过 ``WHERE id = ...`` 查询回来。

本迁移会：
1. 创建数据库备份；
2. 将 NULL id 补为对应 rowid；
3. 重建 sup_supplier，使 id 成为 INTEGER PRIMARY KEY AUTOINCREMENT；
4. 保留现有数据、索引和触发器；
5. 执行 foreign_key_check。
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime

from sqlalchemy import text

from app.database import engine


TABLE = "sup_supplier"
REPAIR_TABLE = "sup_supplier__repair"
COLUMNS = [
    "id",
    "dept_id",
    "supplier_code",
    "supplier_name",
    "region",
    "source_location",
    "invoice_type",
    "tax_rate",
    "supply_cycle_days",
    "return_policy",
    "payment_terms",
    "status",
    "created_at",
    "updated_at",
    "platform",
    "wechat_id",
    "wechat_nickname",
    "is_dropship",
    "supply_mode",
    "supplier_wechat",
]


def _quote_identifier(value: str) -> str:
    """仅用于本文件内固定标识符的安全引用。"""
    return '"' + value.replace('"', '""') + '"'


def _backup_database() -> str:
    """在迁移前创建同目录备份，失败时阻止迁移继续。"""
    database_url = str(engine.url)
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError(f"该迁移只支持 SQLite，当前数据库为: {database_url}")

    db_path = database_url.removeprefix("sqlite:///")
    if not os.path.isfile(db_path):
        raise RuntimeError(f"数据库文件不存在: {db_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.before_supplier_pk_{timestamp}.bak"
    shutil.copy2(db_path, backup_path)
    return backup_path


def upgrade() -> None:
    """执行供应商主键修复。"""
    backup_path = _backup_database()

    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        # SQLAlchemy 2.x 可能因 PRAGMA 开启了隐式事务；先提交该设置，
        # 再显式开启迁移事务，否则 connection.begin() 会报事务已存在。
        connection.commit()
        transaction = connection.begin()
        try:
            table_exists = connection.execute(
                text(
                    "SELECT 1 FROM sqlite_master "
                    "WHERE type='table' AND name=:name"
                ),
                {"name": TABLE},
            ).scalar()
            if not table_exists:
                transaction.rollback()
                return

            columns = {
                row[1]
                for row in connection.exec_driver_sql(
                    f"PRAGMA table_info({_quote_identifier(TABLE)})"
                ).fetchall()
            }
            missing = set(COLUMNS) - columns
            if missing:
                raise RuntimeError(f"sup_supplier 缺少字段: {sorted(missing)}")

            required_nulls = connection.execute(
                text(
                    "SELECT COUNT(*) FROM sup_supplier "
                    "WHERE dept_id IS NULL OR supplier_code IS NULL "
                    "OR supplier_name IS NULL"
                )
            ).scalar_one()
            if required_nulls:
                raise RuntimeError(
                    f"sup_supplier 存在 {required_nulls} 条必填字段为空，"
                    "请先修复数据后再迁移"
                )

            id_conflicts = connection.execute(
                text(
                    "SELECT COALESCE(id, rowid) AS repaired_id, COUNT(*) "
                    "FROM sup_supplier GROUP BY repaired_id HAVING COUNT(*) > 1"
                )
            ).fetchall()
            if id_conflicts:
                raise RuntimeError(
                    "修复后的 id 存在冲突，拒绝自动重建: "
                    + ", ".join(str(row[0]) for row in id_conflicts)
                )

            duplicate_codes = connection.execute(
                text(
                    "SELECT supplier_code FROM sup_supplier "
                    "WHERE supplier_code IS NOT NULL "
                    "GROUP BY supplier_code HAVING COUNT(*) > 1"
                )
            ).fetchall()
            if duplicate_codes:
                codes = [row[0] for row in duplicate_codes]
                raise RuntimeError(
                    "supplier_code 存在重复，拒绝自动重建以避免数据损失: "
                    + ", ".join(map(str, codes))
                )

            preserved_objects = connection.execute(
                text(
                    "SELECT type, name, sql FROM sqlite_master "
                    "WHERE tbl_name=:table AND type IN ('index', 'trigger') "
                    "AND sql IS NOT NULL AND name NOT LIKE 'sqlite_autoindex%'"
                ),
                {"table": TABLE},
            ).fetchall()

            connection.exec_driver_sql(f"DROP TABLE IF EXISTS {_quote_identifier(REPAIR_TABLE)}")
            connection.exec_driver_sql(
                f"""
                CREATE TABLE {_quote_identifier(REPAIR_TABLE)} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dept_id VARCHAR(10) NOT NULL,
                    supplier_code VARCHAR(50) NOT NULL UNIQUE,
                    supplier_name VARCHAR(200) NOT NULL,
                    region VARCHAR(100),
                    source_location VARCHAR(200),
                    invoice_type INTEGER,
                    tax_rate DECIMAL(5, 2),
                    supply_cycle_days INTEGER,
                    return_policy TEXT,
                    payment_terms VARCHAR(100),
                    status INTEGER DEFAULT 1,
                    created_at DATETIME,
                    updated_at DATETIME,
                    platform VARCHAR(20),
                    wechat_id VARCHAR(100),
                    wechat_nickname VARCHAR(100),
                    is_dropship BOOLEAN NOT NULL DEFAULT 0,
                    supply_mode VARCHAR(50),
                    supplier_wechat VARCHAR(100)
                )
                """
            )

            column_sql = ", ".join(_quote_identifier(column) for column in COLUMNS)
            source_id = "COALESCE(id, rowid)"
            connection.exec_driver_sql(
                f"""
                INSERT INTO {_quote_identifier(REPAIR_TABLE)} ({column_sql})
                SELECT {source_id}, {', '.join(_quote_identifier(c) for c in COLUMNS[1:])}
                FROM {_quote_identifier(TABLE)}
                ORDER BY rowid
                """
            )

            connection.exec_driver_sql(f"DROP TABLE {_quote_identifier(TABLE)}")
            connection.exec_driver_sql(
                f"ALTER TABLE {_quote_identifier(REPAIR_TABLE)} "
                f"RENAME TO {_quote_identifier(TABLE)}"
            )

            for object_type, object_name, object_sql in preserved_objects:
                try:
                    connection.exec_driver_sql(object_sql)
                except Exception as exc:
                    raise RuntimeError(
                        f"恢复 {object_type} {object_name} 失败: {exc}"
                    ) from exc

            foreign_key_errors = connection.exec_driver_sql(
                "PRAGMA foreign_key_check"
            ).fetchall()
            if foreign_key_errors:
                raise RuntimeError(
                    f"外键检查失败，共 {len(foreign_key_errors)} 条记录，备份保留于: {backup_path}"
                )

            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")


if __name__ == "__main__":
    upgrade()
