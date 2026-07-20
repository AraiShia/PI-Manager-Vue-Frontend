"""供应商平台分类 — 接口级测试（路由层 HTTP 422 校验）

仅测试 CRUD 函数中的 ValueError 是不够的：路由层必须把业务校验失败转成
HTTPException(422, ...)，前端拦截器才能拿到结构化的 detail 字段。

覆盖：
- /api/suppliers/find-or-create  (platform 必填 / 空白名 / 无效 platform)
- /api/suppliers/{id} PUT         (platform 变更锁定)
- /api/purchase-orders/1688       (supplier_id 关联校验：存在 / 部门 / NULL 平台 / 平台不一致 / 空白名)
"""
import os
import sys

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

# 在导入 main 之前安装 dependency override，避免 get_db 命中真实数据库
install_test_db_dependency()
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_db():
    create_test_db()
    yield
    drop_test_db()


def _seed_supplier(db, *, dept_id: str, platform, supplier_code: str, supplier_name: str = "测试供应商"):
    """绕过校验直接插入测试用供应商（包含新增的 platform 列）"""
    from models import SupSupplier
    s = SupSupplier(
        dept_id=dept_id,
        supplier_code=supplier_code,
        supplier_name=supplier_name,
        platform=platform,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# --- /api/suppliers/find-or-create ---

def test_find_or_create_missing_platform_returns_422():
    """缺失 platform → 422（Literal 必填字段，Pydantic 自动拦截）"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "测试店",
        "dept_id": "S",
        # platform 故意不传
    })
    assert r.status_code == 422, r.text
    assert "platform" in str(r.json())


def test_find_or_create_invalid_platform_returns_422():
    """platform 取值非法 → 422（Literal 校验）"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "测试店",
        "dept_id": "S",
        "platform": "taobao",
    })
    assert r.status_code == 422, r.text


def test_find_or_create_blank_supplier_name_returns_422():
    """纯空白 supplier_name → 422"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "   ",
        "dept_id": "S",
        "platform": "1688",
    })
    assert r.status_code == 422, r.text
    assert "supplier_name" in r.json()["detail"]


def test_find_or_create_1688_missing_shop_link_returns_422():
    """1688 平台未传 shop_link → 422（运行时校验）"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "1688 缺链接店",
        "dept_id": "S",
        "platform": "1688",
        # shop_link 故意不传
    })
    assert r.status_code == 422, r.text
    assert "店铺链接" in r.json()["detail"]


def test_find_or_create_1688_with_shop_link_succeeds():
    """1688 + shop_link 正常创建 → 200，created=True"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "1688 正常店",
        "dept_id": "S",
        "platform": "1688",
        "shop_link": "https://shop.1688.com/x",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] is True
    assert body["supplier_name"] == "1688 正常店"


def test_find_or_create_hits_existing_returns_created_false():
    """命中已有供应商 → 200，created=False"""
    # 先创建一个供应商
    r1 = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "复用测试店",
        "dept_id": "S",
        "platform": "wechat",
        "wechat_id": "wx_test",
    })
    assert r1.status_code == 200
    assert r1.json()["created"] is True
    supplier_id = r1.json()["id"]

    # 再次调用同一名称+平台，应命中并返回 created=False
    r2 = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "复用测试店",
        "dept_id": "S",
        "platform": "wechat",
    })
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["created"] is False
    assert body["id"] == supplier_id  # 复用同一个


# --- /api/suppliers/{id} PUT ---

def test_update_platform_change_blocked_returns_422():
    """已存在 platform 的供应商，update 时改 platform → 422"""
    db = TestingSessionLocal()
    try:
        s = _seed_supplier(db, dept_id="S", platform="1688", supplier_code="SPX001")
        supplier_id = s.id
    finally:
        db.close()

    r = client.put(f"/api/suppliers/{supplier_id}", json={
        "platform": "wechat",   # 试图变更
    })
    assert r.status_code == 422, r.text
    assert "不可修改" in r.json()["detail"]


def test_update_fill_null_platform_allowed():
    """历史供应商 platform=NULL，可首次设置 → 200"""
    db = TestingSessionLocal()
    try:
        s = _seed_supplier(db, dept_id="S", platform=None, supplier_code="SPX002")
        supplier_id = s.id
    finally:
        db.close()

    r = client.put(f"/api/suppliers/{supplier_id}", json={
        "platform": "offline",
    })
    assert r.status_code == 200, r.text
    assert r.json()["platform"] == "offline"


# --- /api/purchase-orders/1688 关联校验（设计文档规格）---

def test_purchase_missing_supplier_id_and_name_returns_422():
    """supplier_id 与 supplier_name 都缺失 → 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "items": [],
    })
    assert r.status_code == 422, r.text


def test_purchase_blank_supplier_name_returns_422():
    """supplier_name 是纯空白 → 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": None,
        "supplier_name": "   ",
        "items": [],
    })
    assert r.status_code == 422, r.text


def test_purchase_supplier_id_wrong_dept_returns_422():
    """supplier.dept_id 与 payload.dept_id 不一致 → 422（部门一致性）"""
    db = TestingSessionLocal()
    try:
        s = _seed_supplier(db, dept_id="A", platform="1688", supplier_code="SPX003")
        supplier_id = s.id
    finally:
        db.close()

    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "B",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier_id,
        "items": [],
    })
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert "部门" in detail
    assert "A" in detail and "B" in detail


def test_purchase_supplier_id_null_platform_returns_422():
    """历史供应商 platform=NULL → 422（不允许直接关联到线上采购）"""
    db = TestingSessionLocal()
    try:
        s = _seed_supplier(db, dept_id="S", platform=None, supplier_code="SPX004")
        supplier_id = s.id
    finally:
        db.close()

    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier_id,
        "items": [],
    })
    assert r.status_code == 422, r.text
    assert "尚未分配平台" in r.json()["detail"]


def test_purchase_supplier_id_platform_mismatch_returns_422():
    """供应商 platform=wechat，但采购 platform=1688 → 422"""
    db = TestingSessionLocal()
    try:
        s = _seed_supplier(db, dept_id="S", platform="wechat", supplier_code="SPX005")
        supplier_id = s.id
    finally:
        db.close()

    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier_id,
        "items": [],
    })
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert "wechat" in detail and "1688" in detail


def test_purchase_unknown_supplier_id_returns_422():
    """supplier_id 不存在 → 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": 999999,
        "items": [],
    })
    assert r.status_code == 422, r.text
    assert "不存在" in r.json()["detail"]