"""产品-供应商-URL 接口测试

覆盖：
- GET  /api/product-supplier-urls         (按 product_id 查询，排序)
- POST /api/product-supplier-urls          (新建 / 重复返回 / is_default 升级 / supplier_id 必填 / URL 协议校验)
- PUT  /api/product-supplier-urls/{id}    (冲突 409 / 历史只读 409)
- DELETE /api/product-supplier-urls/{id}  (默认升级 / 历史只读 409)
- supplier_id 贯穿采购链路
- 采购失败事务回滚
"""
import os
import sys
import time

import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests._helpers import (
    TestingSessionLocal,
    create_test_db,
    drop_test_db,
    install_test_db_dependency,
)
from sqlalchemy import text

install_test_db_dependency()
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_db():
    create_test_db()
    yield
    drop_test_db()


def _seed_product(db, product_id: int, dept_id: str = "D001"):
    """直接插入产品记录"""
    db.execute(text("""
        INSERT INTO prd_customer_product (id, dept_id, customer_id)
        VALUES (:id, :dept_id, 1)
    """), {"id": product_id, "dept_id": dept_id})
    db.commit()


def _seed_supplier(db, supplier_id: int, dept_id: str, platform: str = "1688"):
    """直接插入供应商记录"""
    db.execute(text("""
        INSERT INTO sup_supplier (id, dept_id, supplier_name, supplier_code, platform)
        VALUES (:id, :dept_id, :name, :code, :platform)
    """), {
        "id": supplier_id,
        "dept_id": dept_id,
        "name": f"供应商{supplier_id}",
        "code": f"S{supplier_id}",
        "platform": platform,
    })
    db.commit()


# ---- GET ----

def test_list_urls_returns_sorted_list(client, _reset_db):
    """List 应返回按 is_default DESC, created_at DESC 排序"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    # 插入两条 URL
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, 1, 'A', 'https://x1.com', 1)
    """), )
    time.sleep(0.01)
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, 1, 'A', 'https://x2.com', 0)
    """))
    db.commit()
    db.close()

    r = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1")
    assert r.status_code == 200
    rs = r.json()
    assert len(rs) == 2
    assert rs[0]["is_default"] is True
    assert rs[0]["url"] == "https://x1.com"


# ---- POST ----

def test_create_url_then_duplicate_returns_200(client, _reset_db):
    """POST 相同 URL 不报错，返回已有记录（200）"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    db.close()

    payload = {"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x.com"}
    r1 = client.post("/api/product-supplier-urls", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/product-supplier-urls", json=payload)
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_create_url_with_is_default_promotes(client, _reset_db):
    """POST is_default=true 自动取消其他默认"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    db.close()

    p1 = {"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x1.com", "is_default": True}
    p2 = {"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x2.com", "is_default": True}
    client.post("/api/product-supplier-urls", json=p1)
    client.post("/api/product-supplier-urls", json=p2)
    rs = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1").json()
    defaults = [u for u in rs if u["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["url"] == "https://x2.com"


def test_post_without_supplier_id_returns_422(client, _reset_db):
    """新建必须传 supplier_id"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    db.close()

    r = client.post("/api/product-supplier-urls", json={
        "product_id": 1,
        "supplier_name": "A",
        "url": "https://x.com",
    })
    assert r.status_code == 422


def test_create_url_invalid_protocol_returns_422(client, _reset_db):
    """URL 必须以 http:// 或 https:// 开头"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    db.close()

    r = client.post("/api/product-supplier-urls", json={
        "product_id": 1,
        "supplier_id": 1,
        "supplier_name": "Test",
        "url": "ftp://invalid.com",
    })
    assert r.status_code == 422


# ---- PUT ----

def test_update_url_conflict_returns_409(client, _reset_db):
    """PUT URL 与同 product+supplier 另一条 URL 冲突时返回 409"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, 1, 'A', 'https://a.com', 0)
    """))
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, 1, 'A', 'https://b.com', 0)
    """))
    db.commit()
    row = db.execute(text("SELECT id FROM prd_product_supplier_url WHERE url='https://b.com'")).fetchone()
    uid = row[0]
    db.close()

    response = client.put(f"/api/product-supplier-urls/{uid}", json={"url": "https://a.com"})
    assert response.status_code == 409


# ---- DELETE ----

def test_delete_default_auto_promotes_latest(client, _reset_db):
    """删除默认 URL 后，最新一条自动成为默认"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    _seed_supplier(db, 1, "D001")
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, 1, 'A', 'https://x1.com', 1)
    """))
    db.commit()
    row1 = db.execute(text("SELECT id FROM prd_product_supplier_url WHERE url='https://x1.com'")).fetchone()
    id1 = row1[0]
    db.close()

    time.sleep(0.01)
    client.post("/api/product-supplier-urls", json={
        "product_id": 1, "supplier_id": 1, "supplier_name": "A",
        "url": "https://x2.com", "is_default": True,
    })

    client.delete(f"/api/product-supplier-urls/{id1}")
    rs = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1").json()
    assert len(rs) == 1
    assert rs[0]["url"] == "https://x2.com"
    assert rs[0]["is_default"] is True


def test_delete_null_supplier_id_history_returns_409(client, _reset_db):
    """supplier_id 为 NULL 的历史数据不允许 DELETE"""
    db = TestingSessionLocal()
    _seed_product(db, 1)
    db.execute(text("""
        INSERT INTO prd_product_supplier_url
            (product_id, supplier_id, supplier_name, url, is_default)
        VALUES (1, NULL, '历史供应商', 'https://history.com', 0)
    """))
    db.commit()
    row = db.execute(text("SELECT id FROM prd_product_supplier_url WHERE url='https://history.com'")).fetchone()
    history_id = row[0]
    db.close()

    r = client.delete(f"/api/product-supplier-urls/{history_id}")
    assert r.status_code == 409


# ---- 采购链路 ----

def test_supplier_id_threads_through_1688_batch(client, _reset_db):
    """验证 create_1688_purchase_batch 写入 supplier_id + URL 历史"""
    db = TestingSessionLocal()
    _seed_product(db, 10, "D001")
    _seed_supplier(db, 20, "D001", "1688")
    # 插入 PI（pi_id=100）
    db.execute(text("""
        INSERT INTO pi_proforma_invoice (id, dept_id, pi_number, customer_id)
        VALUES (100, 'D001', 'PI-001', 1)
    """))
    db.commit()
    db.close()

    target_url = "https://detail.1688.com/offer/abc.html"
    payload = {
        "dept_id": "D001",
        "pi_id": 100,
        "platform": "1688",
        "supplier_id": 20,
        "supplier_name": "供应商20",
        "items": [{
            "product_id": 10,
            "supplier_name": "供应商20",
            "link": target_url,
            "unit_price": 10.0,
            "quantity": 1,
        }],
    }
    r = client.post("/api/purchase-orders/1688", json=payload)
    assert r.status_code in (200, 201), f"期望 200/201，实际 {r.status_code}: {r.text}"
    body = r.json()
    assert body.get("success") is True

    # 验证 po_1688_purchase.supplier_id
    db = TestingSessionLocal()
    po_row = db.execute(text(
        "SELECT supplier_id FROM po_1688_purchase WHERE product_id=:pid ORDER BY id DESC LIMIT 1"
    ), {"pid": 10}).fetchone()
    db.close()
    assert po_row is not None and po_row[0] == 20, f"期望 supplier_id=20，实际 {po_row}"

    # 验证 prd_product_supplier_url
    db = TestingSessionLocal()
    url_row = db.execute(text(
        "SELECT supplier_id FROM prd_product_supplier_url WHERE product_id=:pid AND url=:u"
    ), {"pid": 10, "u": target_url}).fetchone()
    db.close()
    assert url_row is not None and url_row[0] == 20


def test_1688_batch_failure_rolls_back_urls(client, _reset_db):
    """验证采购单生成失败时，URL 历史也回滚（事务统一）"""
    db = TestingSessionLocal()
    _seed_product(db, 10, "D001")
    db.commit()
    db.close()

    target_url = "https://detail.1688.com/offer/rollback.html"
    payload = {
        "dept_id": "D001",
        "pi_id": 101,
        "platform": "1688",
        "supplier_id": 99999,  # 不存在的 supplier_id
        "supplier_name": "幽灵供应商",
        "items": [{
            "product_id": 10,
            "supplier_name": "幽灵供应商",
            "link": target_url,
            "unit_price": 1.0,
            "quantity": 1,
        }],
    }
    r = client.post("/api/purchase-orders/1688", json=payload)
    assert r.status_code >= 400, f"期望 4xx/5xx，实际 {r.status_code}"

    db = TestingSessionLocal()
    url_row = db.execute(text(
        "SELECT id FROM prd_product_supplier_url WHERE url=:u"
    ), {"u": target_url}).fetchone()
    db.close()
    assert url_row is None, "事务回滚后不应残留 URL 历史"
