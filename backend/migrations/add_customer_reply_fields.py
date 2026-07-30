"""为 customer_replies 补齐客户往来记录字段。"""

import os
import sys

from sqlalchemy import inspect, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import engine


def upgrade():
    # 客户往来功能可能是在旧数据库上首次启用；此时整张表还不存在，
    # 先按当前模型创建它，再兼容已有旧表的补列场景。
    if "customer_replies" not in inspect(engine).get_table_names():
        from models.customer_reply import CustomerReply

        CustomerReply.__table__.create(bind=engine, checkfirst=True)
        return

    # 旧版本已创建 customer_replies 表，但模型后来增加了这些字段。
    # SQLite 不支持 IF NOT EXISTS，因此按列逐个执行并兼容重复执行。
    statements = [
        "ALTER TABLE customer_replies ADD COLUMN reply_type VARCHAR(50) NOT NULL DEFAULT 'reply'",
        "ALTER TABLE customer_replies ADD COLUMN submitter_name VARCHAR(100)",
        "ALTER TABLE customer_replies ADD COLUMN sequence_num INTEGER",
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
