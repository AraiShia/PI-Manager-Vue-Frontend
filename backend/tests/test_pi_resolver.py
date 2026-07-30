import sys
from pathlib import Path

# 将 backend 目录加入 sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database import Base, get_db
from models import PiProformaInvoice
from crud.pi import resolve_pi

# 使用内存 SQLite 数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # 插入测试数据
    test_pi = PiProformaInvoice(
        id=100,
        pi_no="PISO9J02607280",
        dept_id="S",
        customer_id=1,
        total_amount=1000.0,
    )
    db.add(test_pi)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)


def test_resolve_pi_by_id():
    """测试通过数字 ID 解析 PI"""
    db = TestingSessionLocal()
    pi_by_int = resolve_pi(db, 100)
    assert pi_by_int is not None
    assert pi_by_int.pi_no == "PISO9J02607280"

    pi_by_str_int = resolve_pi(db, "100")
    assert pi_by_str_int is not None
    assert pi_by_str_int.pi_no == "PISO9J02607280"


def test_resolve_pi_by_no():
    """测试通过 PI 编号 (字符串) 解析 PI"""
    db = TestingSessionLocal()
    pi_by_no = resolve_pi(db, "PISO9J02607280")
    assert pi_by_no is not None
    assert pi_by_no.id == 100


def test_resolve_pi_not_found():
    """测试解析不存在的 ID 或 编号"""
    db = TestingSessionLocal()
    assert resolve_pi(db, "NON_EXISTENT") is None
    assert resolve_pi(db, 99999) is None


def test_api_customer_replies_by_pi_no():
    """测试通过 PI 编号调用 GET /api/customer-replies/pi/{pi_no} 不再返回 422 错误"""
    # 传入 PI 编号
    response = client.get("/api/customer-replies/pi/PISO9J02607280")
    assert response.status_code == 200
    assert response.json() == []


def test_api_customer_replies_by_pi_id():
    """测试通过数字 ID 调用 GET /api/customer-replies/pi/{pi_id} 返回 200"""
    response = client.get("/api/customer-replies/pi/100")
    assert response.status_code == 200
    assert response.json() == []


def test_api_customer_replies_list_by_pi_no():
    """测试通过 PI 编号调用 GET /api/customer-replies/pi/{pi_no}/list"""
    response = client.get("/api/customer-replies/pi/PISO9J02607280/list")
    assert response.status_code == 200
    data = response.json()
    assert data["pi_id"] == 100
    assert data["pi_no"] == "PISO9J02607280"
