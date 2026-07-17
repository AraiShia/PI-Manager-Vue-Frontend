"""
测试帮助函数：内存 SQLite + 表创建 + get_db 替换

不引入 conftest.py，方便按需调用。
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app

# StaticPool 确保 :memory: SQLite 在同一进程的所有线程间共享连接，
# 避免 TestClient 在不同线程执行请求时出现 "no such table" 错误。
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def create_test_db() -> None:
    """每个测试方法/类调用一次，建表。"""
    Base.metadata.create_all(bind=_engine)


def drop_test_db() -> None:
    """测试结束清理。"""
    Base.metadata.drop_all(bind=_engine)


def get_test_db():
    """yield 一个测试 session。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def install_test_db_dependency() -> None:
    """把 FastAPI app 的 get_db 替换为测试版。"""
    app.dependency_overrides[get_db] = get_test_db
