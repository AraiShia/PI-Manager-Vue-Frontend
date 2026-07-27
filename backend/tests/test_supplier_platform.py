"""供应商平台分类 — CRUD 单元测试

CRUD 层是唯一业务校验层：platform 锁定 / find-or-create 语义等。
均通过 pytest.raises(ValueError) 验证。
路由层测试见 test_supplier_platform_api.py（断言 HTTP 422）。
"""
import pytest
import sys
import os

# 添加 backend 到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from models import SupSupplier
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from crud.supplier import (
    create_supplier, update_supplier,
    find_or_create_supplier_by_name,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def insert_supplier(db):
    def _insert(supplier_name: str, platform: str | None = None, **kwargs):
        s = SupSupplier(
            supplier_name=supplier_name,
            dept_id=kwargs.get("dept_id", "S"),
            supplier_code=f"SP{kwargs.get('seq', 1):03d}",
            platform=platform,
            wechat_id=kwargs.get("wechat_id"),
            wechat_nickname=kwargs.get("wechat_nickname"),
            is_dropship=kwargs.get("is_dropship", False),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s
    return _insert


# --- create_supplier 平台校验 ---

def test_create_online_ok(db):
    payload = SupplierCreate(supplier_name="线上店", platform="online")
    s = create_supplier(db, payload)
    assert s.platform == "online"


def test_create_offline_ok(db):
    payload = SupplierCreate(supplier_name="线下店", platform="offline")
    s = create_supplier(db, payload)
    assert s.platform == "offline"


def test_response_includes_platform_fields(db):
    payload = SupplierCreate(supplier_name="wx123", platform="online", wechat_nickname="昵称")
    s = create_supplier(db, payload)
    r = SupplierResponse.model_validate(s)
    assert r.platform == "online"
    assert r.wechat_nickname == "昵称"


# --- find_or_create 返回值语义 ---

def test_find_or_create_creates_new(db):
    supplier, created = find_or_create_supplier_by_name(
        db, "线上店A", platform="online"
    )
    assert created is True
    assert supplier.platform == "online"


def test_find_or_create_hits_existing(db, insert_supplier):
    s1 = insert_supplier("线上店B", platform="online")
    supplier, created = find_or_create_supplier_by_name(
        db, "线上店B", platform="online"
    )
    assert created is False
    assert supplier.id == s1.id


def test_find_or_create_fills_wechat_fields(db, insert_supplier):
    s1 = insert_supplier("线上店C", platform="online")
    supplier, created = find_or_create_supplier_by_name(
        db, "线上店C", platform="online", wechat_id="wx_new"
    )
    assert created is False
    assert supplier.wechat_id == "wx_new"


# --- update_supplier 平台锁定 ---

def test_update_blocked_when_changing_existing_platform(db, insert_supplier):
    s = insert_supplier("线上店D", platform="online")
    update = SupplierUpdate(platform="offline")
    with pytest.raises(ValueError, match="不可修改"):
        update_supplier(db, s.id, update)


def test_update_allows_first_time_platform_set(db, insert_supplier):
    s = insert_supplier("历史店", platform=None)
    update = SupplierUpdate(platform="offline")
    result = update_supplier(db, s.id, update)
    assert result.platform == "offline"


# --- 采购单 CRUD 业务校验 ---

def test_purchase_rejects_missing_supplier_id_and_name(db):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="online",
        supplier_id=None, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="supplier_id.*supplier_name"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_null_platform_supplier(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("历史店", platform=None, seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="online",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="尚未分配平台"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_wrong_dept(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("A部门店", platform="online", dept_id="A", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="B", pi_id=1, platform="online",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="部门.*不一致"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_platform_mismatch(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("线下店", platform="offline", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="online",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="平台.*不一致"):
        resolve_online_supplier(db, payload)


def test_purchase_accepts_valid_supplier_id(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("线上店E", platform="online", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="online",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    supplier_id = resolve_online_supplier(db, payload)
    assert supplier_id == s.id


def test_purchase_creates_supplier_when_name_only(db):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="online",
        supplier_id=None, supplier_name="新线上店",
        items=[]
    )
    supplier_id = resolve_online_supplier(db, payload)
    assert supplier_id is not None

    # 验证供应商已创建
    s = db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first()
    assert s is not None
    assert s.supplier_name == "新线上店"
    assert s.platform == "online"
