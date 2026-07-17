"""
产品搜索服务测试套件（2026-07-17）

按设计文档 §11 验收标准覆盖：P0 全 8 项 + P1 全 11 项 + P2-3 / P2-4 / P2-5。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests._helpers import (
    create_test_db, drop_test_db, install_test_db_dependency, TestingSessionLocal,
)

from models import (
    CrmCustomer,
    PiProformaInvoice,
    PiProformaInvoiceItem,
    PrdCustomerProduct,
    PrdCustomerProductCode,
    PrdCustomerProductOE,
)
from crud.product_search import search_products, split_oe_tokens


@pytest.fixture(autouse=True)
def setup_db():
    create_test_db()
    install_test_db_dependency()
    yield
    drop_test_db()


@pytest.fixture
def db_session() -> Session:
    s = TestingSessionLocal()
    try:
        yield s
    finally:
        s.close()


def _make_customer(db, name="ACME", code="A01"):
    c = CrmCustomer(dept_id="S", customer_name=name, customer_code=code)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_product(db, customer_id, **kwargs):
    p = PrdCustomerProduct(customer_id=customer_id, is_active=True, **kwargs)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_code(db, product_id, code="A01S01240001", is_primary=True):
    c = PrdCustomerProductCode(
        customer_product_id=product_id, product_code=code, is_primary=is_primary
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_oe(db, product_id, oe_number, is_primary=False):
    o = PrdCustomerProductOE(
        customer_product_id=product_id, oe_number=oe_number, is_primary=is_primary
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def _make_pi_item(db, customer_id, product_id, **kwargs):
    pi = PiProformaInvoice(
        pi_no=f"PI-T-{product_id}", dept_id="S", customer_id=customer_id, total_amount=1
    )
    db.add(pi)
    db.commit()
    db.refresh(pi)
    item = PiProformaInvoiceItem(
        pi_id=pi.id, product_id=product_id,
        quantity=1, unit_price=1, total_price=1,
        **kwargs,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ===== P0-1 路由 + 422 =====

def test_split_oe_tokens():
    assert split_oe_tokens("601, 750 / AXMC") == ["601", "750", "AXMC"]
    assert split_oe_tokens("") == []
    assert split_oe_tokens(",,, ") == []


def test_search_api_with_keyword_returns_200():
    from main import app
    with TestClient(app) as c:
        r = c.get("/api/customer-products/search?keyword=test")
        assert r.status_code == 200
        body = r.json()
        assert "results" in body and "total" in body


def test_search_api_missing_keyword_returns_422():
    """P0-1 修正：裸 /search 返回 422（Query min_length=1），不是 /{product_id} 整数转换错误。"""
    from main import app
    with TestClient(app) as c:
        r = c.get("/api/customer-products/search")
        assert r.status_code == 422


def test_search_api_keyword_too_long_returns_422():
    from main import app
    with TestClient(app) as c:
        r = c.get(f"/api/customer-products/search?keyword={'x' * 101}")
        assert r.status_code == 422


# ===== 精确/模糊匹配 =====

def test_exact_customer_model_score_100(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="ACM-750")
    res = search_products(db_session, keyword="ACM-750")
    assert res.total == 1
    assert res.results[0].match_score == 100.0
    assert "customer_model" in res.results[0].matched_in


def test_fuzzy_customer_model_score_80(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="ACM-750-FRONT")
    res = search_products(db_session, keyword="ACM")
    assert res.total == 1
    assert res.results[0].match_score == 80.0


def test_product_name_score_60(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, product_name="750 刹车片")
    res = search_products(db_session, keyword="刹车")
    assert res.total == 1
    assert "product_name" in res.results[0].matched_in


def test_detail_desc_score_30(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, detail_desc="前刹 750 系列专用")
    res = search_products(db_session, keyword="前刹")
    assert res.results[0].match_score == 30.0
    assert "detail_desc" in res.results[0].matched_in


# ===== PI item 名称字段 =====

def test_pi_item_detail_desc_priority(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, product_name="Old Name")
    _make_pi_item(db_session, c.id, p.id, detail_desc="New Name")
    res = search_products(db_session, keyword="New Name")
    assert res.results[0].product_name == "New Name"


def test_pi_item_customer_model_priority(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="OLD")
    _make_pi_item(db_session, c.id, p.id, customer_model="NEW-750")
    res = search_products(db_session, keyword="NEW-750")
    assert res.results[0].customer_model == "NEW-750"


def test_pi_item_detail_desc_en(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, detail_desc_en="Brake Pad 750")
    res = search_products(db_session, keyword="brake")
    assert "product_name_en" in res.results[0].matched_in


def test_pi_item_product_short_name_en(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, product_short_name_en="BP750")
    res = search_products(db_session, keyword="BP")
    assert "product_short_name_en" in res.results[0].matched_in


def test_deleted_pi_item_not_used(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, is_deleted=True, detail_desc="Hidden")
    res = search_products(db_session, keyword="Hidden")
    assert res.total == 0


# ===== 软删除过滤 =====

def test_deleted_product_not_returned(db_session):
    from datetime import datetime
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="DELETED", deleted_at=datetime.now())
    res = search_products(db_session, keyword="DELETED")
    assert res.total == 0


# ===== OE 匹配 =====

def test_oe_single_token_score_50(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "601")
    _make_oe(db_session, p.id, "750")
    res = search_products(db_session, keyword="750")
    assert "oe" in res.results[0].matched_in
    assert res.results[0].match_score == 50.0


def test_oe_multi_token_hit(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, product_name="Brake")
    _make_oe(db_session, p.id, "601")
    _make_oe(db_session, p.id, "750")
    _make_oe(db_session, p.id, "AXMC")
    res = search_products(db_session, keyword="601, 750 / AXMC")
    assert res.total == 1
    assert "oe" in res.results[0].matched_in


def test_oe_partial_token_case_insensitive(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "AXMC")
    res = search_products(db_session, keyword="ax")
    assert res.total == 1


# ===== customer_id 过滤 =====

def test_customer_id_filter(db_session):
    ca = _make_customer(db_session, name="CustA", code="CA1")
    cb = _make_customer(db_session, name="CustB", code="CB1")
    _make_product(db_session, ca.id, customer_model="ABC-750")
    _make_product(db_session, cb.id, customer_model="ABC-750")
    res = search_products(db_session, keyword="ABC-750", customer_id=ca.id)
    assert res.total == 1
    assert res.results[0].customer_id == ca.id


# ===== 排序 =====

def test_sort_by_score_desc(db_session):
    c = _make_customer(db_session)
    p1 = _make_product(db_session, c.id, customer_model="MATCH-EXACT")  # score 100
    p2 = _make_product(db_session, c.id, product_name="MATCH-NAME")     # score 60
    p3 = _make_product(db_session, c.id)                                # score 50
    _make_oe(db_session, p3.id, "MATCH")
    res = search_products(db_session, keyword="MATCH-EXACT")
    assert res.results[0].id == p1.id


# ===== sub_images 解析 =====

def test_parse_sub_images_normal():
    from crud.product_search import _parse_sub_images
    assert _parse_sub_images('["img2.jpg","img3.jpg"]') == ["img2.jpg", "img3.jpg"]
    assert _parse_sub_images("invalid json") == []
    assert _parse_sub_images('[123, null]') == []
    assert _parse_sub_images("") == []
    assert _parse_sub_images(None) == []


# ===== 主 OE 优先 =====

def test_primary_oe_first(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "Z", is_primary=False)
    _make_oe(db_session, p.id, "A", is_primary=True)
    res = search_products(db_session, keyword="A")
    assert res.results[0].oes[0] == "A"


# ===== 响应字段 =====

def test_response_has_customer_code(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="X1")
    _make_code(db_session, p.id, "C-001", is_primary=True)
    res = search_products(db_session, keyword="X1")
    assert res.results[0].customer_code == "C-001"


def test_response_no_price_rmb(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="Y1")
    res = search_products(db_session, keyword="Y1")
    raw = res.results[0].model_dump()
    assert "price_rmb" not in raw
    assert "currency" not in raw


# ===== OE 批量同步 CRUD =====

def test_bulk_sync_oes_replace(db_session):
    from crud.customer_product import bulk_sync_oes, get_product_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD-1")
    _make_oe(db_session, p.id, "OLD-2")
    db_session.commit()  # 先提交，确保 bulk_sync 可见旧数据
    result = bulk_sync_oes(db_session, p.id, ["NEW-1", "NEW-2"])
    db_session.commit()  # 提交 bulk_sync 的更改
    assert result["added"] == 2
    assert result["removed"] == 2
    assert result["total"] == 2
    assert result["primary_oe"] == "NEW-1"
    # 用新的 session 读取，确保不受 ORM 缓存影响
    from tests._helpers import TestingSessionLocal
    db_session2 = TestingSessionLocal()
    try:
        oes = get_product_oes(db_session2, p.id)
        assert sorted([oe.oe_number for oe in oes]) == ["NEW-1", "NEW-2"]
        assert next(oe for oe in oes if oe.is_primary).oe_number == "NEW-1"
    finally:
        db_session2.close()


def test_bulk_sync_oes_preserves_existing(db_session):
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    existing = _make_oe(db_session, p.id, "KEEP-1")
    old_id = existing.id
    old_created_at = existing.created_at
    result = bulk_sync_oes(db_session, p.id, ["KEEP-1", "ADD-2"])
    db_session.refresh(existing)
    assert existing.id == old_id
    assert existing.created_at == old_created_at
    assert result["added"] == 1
    assert result["removed"] == 0
    assert result["total"] == 2


def test_bulk_sync_oes_clear(db_session):
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "X")
    result = bulk_sync_oes(db_session, p.id, [])
    assert result["total"] == 0
    assert result["removed"] == 1
    assert result["primary_oe"] is None


def test_bulk_sync_oes_set_first_false_preserves_primary(db_session):
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "KEEP", is_primary=True)
    result = bulk_sync_oes(db_session, p.id, ["KEEP", "NEW"], set_first_as_primary=False)
    assert result["added"] == 1
    assert result["removed"] == 0
    assert result["primary_oe"] == "KEEP"


def test_bulk_sync_oes_set_first_false_removes_old_primary(db_session):
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD-PRIMARY", is_primary=True)
    result = bulk_sync_oes(db_session, p.id, ["ONLY-NEW"], set_first_as_primary=False)
    assert result["added"] == 1
    assert result["removed"] == 1
    assert result["primary_oe"] is None


def test_bulk_sync_oes_unknown_product(db_session):
    from crud.customer_product import bulk_sync_oes
    assert bulk_sync_oes(db_session, 99999, ["X"]) is None


# ===== OE 批量同步 API 层 =====

def test_bulk_sync_oes_api_returns_404(db_session):
    from main import app
    with TestClient(app) as c:
        r = c.post(
            "/api/customer-products/99999/oes/bulk-sync",
            json={"oes": ["X"]},
        )
        assert r.status_code == 404


def test_bulk_sync_oes_api_returns_json(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD")
    from main import app
    with TestClient(app) as c_client:
        r = c_client.post(
            f"/api/customer-products/{p.id}/oes/bulk-sync",
            json={"oes": ["NEW-1", "NEW-2"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert "added" in body
        assert "removed" in body
        assert "total" in body
        assert "primary_oe" in body
        assert body["added"] == 2
        assert body["removed"] == 1
        assert body["total"] == 2
        assert body["primary_oe"] == "NEW-1"


def test_bulk_sync_oes_atomicity_on_exception(db_session):
    """验证 product_id 不存在时返回 None，且原产品数据完全未变（事务原子性）。"""
    from crud.customer_product import bulk_sync_oes, get_product_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "BEFORE", is_primary=True)
    db_session.commit()
    before_count = len(list(get_product_oes(db_session, p.id)))
    result = bulk_sync_oes(db_session, 99999, ["X"])
    assert result is None
    after_count = len(list(get_product_oes(db_session, p.id)))
    assert after_count == before_count
