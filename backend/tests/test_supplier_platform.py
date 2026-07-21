"""供应商平台分类 — CRUD 单元测试（ValueError 语义）

CRUD 层是唯一业务校验层：platform 校验 / shop_link 必填 / find-or-create 语义 等
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
            shop_link=kwargs.get("shop_link"),
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

def test_create_1688_requires_shop_link(db):
    payload = SupplierCreate(supplier_name="1688店", platform="1688")
    with pytest.raises(ValueError, match="店铺链接"):
        create_supplier(db, payload)


def test_create_1688_with_shop_link_ok(db):
    payload = SupplierCreate(supplier_name="1688店", platform="1688", shop_link="https://shop.1688.com")
    s = create_supplier(db, payload)
    assert s.platform == "1688"
    assert s.shop_link == "https://shop.1688.com"


def test_create_wechat_ok_without_shop_link(db):
    payload = SupplierCreate(supplier_name="wx123", platform="wechat")
    s = create_supplier(db, payload)
    assert s.platform == "wechat"
    assert s.shop_link is None


def test_response_includes_platform_fields(db):
    payload = SupplierCreate(supplier_name="wx123", platform="wechat", wechat_nickname="昵称")
    s = create_supplier(db, payload)
    r = SupplierResponse.model_validate(s)
    assert r.platform == "wechat"
    assert r.wechat_nickname == "昵称"


# --- find_or_create 返回值语义 ---

def test_find_or_create_creates_new(db):
    supplier, created = find_or_create_supplier_by_name(
        db, "1688店A", platform="1688", shop_link="https://shop.1688.com"
    )
    assert created is True
    assert supplier.platform == "1688"


def test_find_or_create_hits_existing(db, insert_supplier):
    s1 = insert_supplier("1688店B", platform="1688")
    supplier, created = find_or_create_supplier_by_name(
        db, "1688店B", platform="1688", shop_link="https://new.1688.com"
    )
    assert created is False
    assert supplier.id == s1.id
    assert supplier.shop_link == "https://new.1688.com"  # 已补齐


def test_find_or_create_raises_when_1688_no_shop_link(db, insert_supplier):
    insert_supplier("1688店C", platform="1688", shop_link=None)
    with pytest.raises(ValueError, match="店铺链接"):
        find_or_create_supplier_by_name(db, "1688店C", platform="1688")


def test_find_or_create_raises_on_invalid_platform(db):
    with pytest.raises(ValueError, match="无效"):
        find_or_create_supplier_by_name(db, "任意店", platform="taobao")


# --- update_supplier 平台锁定 ---

def test_update_blocked_when_changing_existing_platform(db, insert_supplier):
    s = insert_supplier("1688店D", platform="1688", shop_link="https://x.com")
    update = SupplierUpdate(platform="wechat")
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
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=None, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="supplier_id.*supplier_name"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_null_platform_supplier(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("历史店", platform=None, seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="尚未分配平台"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_wrong_dept(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("A部门店", platform="1688", dept_id="A", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="B", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="部门.*不一致"):
        resolve_online_supplier(db, payload)


def test_purchase_rejects_platform_mismatch(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("微信店", platform="wechat", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="平台.*不一致"):
        resolve_online_supplier(db, payload)


def test_purchase_accepts_valid_supplier_id(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    s = insert_supplier("1688店E", platform="1688", shop_link="https://x.com", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    supplier_id = resolve_online_supplier(db, payload)
    assert supplier_id == s.id


def test_purchase_creates_supplier_when_name_only(db):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import resolve_online_supplier
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=None, supplier_name="新1688店",
        shop_link="https://shop.1688.com/new",
        items=[]
    )
    supplier_id = resolve_online_supplier(db, payload)
    assert supplier_id is not None

    # 验证供应商已创建
    s = db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first()
    assert s is not None
    assert s.supplier_name == "新1688店"
    assert s.platform == "1688"
    assert s.shop_link == "https://shop.1688.com/new"
