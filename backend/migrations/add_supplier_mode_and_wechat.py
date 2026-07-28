"""数据库迁移脚本：为 sup_supplier 表安全添加 supply_mode 与 supplier_wechat 字段。

运行方式：
    python backend/migrations/add_supplier_mode_and_wechat.py
"""

import os
import sys
import logging
from sqlalchemy import text

# 将 backend 路径添加到 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import engine

# 配置日志格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def upgrade() -> None:
    """执行数据库升级：幂等添加 supply_mode 和 supplier_wechat 列。"""
    statements = [
        "ALTER TABLE sup_supplier ADD COLUMN supply_mode VARCHAR(50)",
        "ALTER TABLE sup_supplier ADD COLUMN supplier_wechat VARCHAR(100)",
    ]

    with engine.connect() as conn:
        for sql in statements:
            try:
                conn.execute(text(sql))
                logging.info(f"成功执行 SQL: {sql}")
            except Exception as exc:
                err_msg = str(exc).lower()
                # 兼容 MySQL/SQLite 中的列已存在异常 (duplicate column name)
                if "duplicate column name" in err_msg or "already exists" in err_msg:
                    logging.warning(f"列已存在，忽略跳过: {sql}")
                else:
                    logging.error(f"执行 SQL 失败: {sql}, 错误信息: {exc}")
                    raise
        conn.commit()
        logging.info("数据库 sup_supplier 表迁移升级完成！")


if __name__ == "__main__":
    upgrade()
