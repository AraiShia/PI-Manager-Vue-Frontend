"""
产品搜索 CRUD：分字段独立查询 + Python 精排

设计要点（2026-07-17）：
- 不使用 SQL LIMIT 截断候选集；改为分字段查询后合并去重，最后 Python 端按 score 排序。
- 名称字段来源闭环：中文名称/客户型号优先取 pi_item.detail_desc / pi_item.customer_model（用户最新编辑处），
  fallback 到 PrdCustomerProduct 同名字段。
- OE 用 [,\s/、;]+ 拆分多 token，任一 token 子串命中即视为命中。
- 已删除产品（deleted_at）与已删除 PI item（is_deleted=False）必须过滤。
"""
import json
import re
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from models import (
    PiProformaInvoice,
    PiProformaInvoiceItem,
    PrdCustomerProduct,
    PrdCustomerProductOE,
)
from schemas.product_search import ProductSearchItem, ProductSearchResponse

OE_SPLIT_RE = re.compile(r"[,\s/、;]+")


def split_oe_tokens(kw: str) -> list[str]:
    """按 [,\s/、;]+ 拆分关键词，返回去空 token 列表。"""
    return [t for t in OE_SPLIT_RE.split(kw) if t.strip()]


def _parse_sub_images(value) -> list[str]:
    if not isinstance(value, str) or not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, str)]


def _build_code(p: PrdCustomerProduct) -> Optional[str]:
    codes = p.codes or []
    primary = next((c for c in codes if c.is_primary), None)
    if primary:
        return primary.product_code
    return codes[0].product_code if codes else None


def _build_oes(p: PrdCustomerProduct) -> list[str]:
    """主 OE 排第一，保持其他顺序。"""
    records = sorted(
        [oe for oe in (p.oes or []) if oe.oe_number],
        key=lambda oe: not bool(oe.is_primary),
    )
    return [oe.oe_number for oe in records]


def _get_name_fields(p: PrdCustomerProduct, pi_item: Optional[PiProformaInvoiceItem]):
    """名称来源：PI item 优先（用户最近编辑），fallback 到 PrdCustomerProduct。"""
    product_name = (pi_item.detail_desc if pi_item else None) or p.product_name or ""
    customer_model = (pi_item.customer_model if pi_item else None) or p.customer_model or ""
    return product_name, customer_model


def score_product(
    p: PrdCustomerProduct,
    kw: str,
    oe_tokens: list[str],
    latest_pi_item: Optional[PiProformaInvoiceItem],
) -> tuple[float, list[str]]:
    score, matched = 0.0, []
    kwl = kw.lower()
    token_lc = [t.lower() for t in oe_tokens if t]
    product_name, customer_model = _get_name_fields(p, latest_pi_item)

    if customer_model:
        if customer_model == kw:
            score = max(score, 100.0)
            matched.append("customer_model")
        elif kwl in customer_model.lower():
            score = max(score, 80.0)
            matched.append("customer_model")

    if product_name and kwl in product_name.lower():
        score = max(score, 60.0)
        matched.append("product_name")

    if latest_pi_item is not None:
        pi_name_fields = [
            ("product_name_en", getattr(latest_pi_item, "detail_desc_en", None), 55.0),
            ("product_short_name", getattr(latest_pi_item, "product_short_name", None), 45.0),
            ("product_short_name_en", getattr(latest_pi_item, "product_short_name_en", None), 40.0),
        ]
        for key, val, sc in pi_name_fields:
            if val and kwl in str(val).lower():
                score = max(score, sc)
                matched.append(key)

    if p.detail_desc and kwl in p.detail_desc.lower():
        score = max(score, 30.0)
        matched.append("detail_desc")

    oes = [(oe.oe_number or "") for oe in (p.oes or [])]
    if any(any(tok in oe.lower() for tok in token_lc) for oe in oes):
        score = max(score, 50.0)
        matched.append("oe")

    return score, matched


def build_search_item(
    p: PrdCustomerProduct,
    pi_item: Optional[PiProformaInvoiceItem],
    matched: list[str],
    score: float,
) -> ProductSearchItem:
    # matched_in key 映射：PI item 字段 → 响应字段
    pi_name_map = {
        "detail_desc": "product_name",
        "customer_model": "customer_model",
        "detail_desc_en": "product_name_en",
        "product_short_name": "product_short_name",
        "product_short_name_en": "product_short_name_en",
    }
    resolved_matched = [pi_name_map.get(m, m) for m in matched]

    pi_detail_desc = getattr(pi_item, "detail_desc", None) if pi_item else None
    pi_customer_model = getattr(pi_item, "customer_model", None) if pi_item else None

    return ProductSearchItem(
        id=p.id,
        customer_id=p.customer_id,
        customer_name=(p.customer.name if p.customer else "") or "",
        customer_model=(pi_customer_model or p.customer_model or "") or None,
        product_name=(pi_detail_desc or p.product_name or "") or None,
        product_name_en=getattr(pi_item, "detail_desc_en", None) if pi_item else None,
        product_short_name=getattr(pi_item, "product_short_name", None) if pi_item else None,
        product_short_name_en=getattr(pi_item, "product_short_name_en", None) if pi_item else None,
        detail_desc=p.detail_desc or None,
        brand=p.brand,
        customer_code=_build_code(p),
        product_code=p.system_code or None,
        price_usd=float(p.price_usd) if p.price_usd else None,
        image_url=p.image_url or None,
        sub_images=_parse_sub_images(p.sub_images),
        oes=_build_oes(p),
        matched_in=resolved_matched,
        match_score=score,
    )


def search_products(
    db: Session,
    keyword: str,
    customer_id: Optional[int] = None,
    limit: int = 20,
) -> ProductSearchResponse:
    oe_tokens = split_oe_tokens(keyword)
    text_kw = f"%{keyword}%"

    # 1) 客户型号精确匹配
    exact_model_q = db.query(PrdCustomerProduct).filter(
        PrdCustomerProduct.deleted_at.is_(None),
        PrdCustomerProduct.customer_model == keyword,
    )
    if customer_id is not None:
        exact_model_q = exact_model_q.filter(
            PrdCustomerProduct.customer_id == customer_id
        )
    exact_model = exact_model_q.all()

    # 2) PrdCustomerProduct 文本字段模糊匹配
    text_match_q = db.query(PrdCustomerProduct).filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(
            PrdCustomerProduct.product_name.ilike(text_kw),
            PrdCustomerProduct.detail_desc.ilike(text_kw),
        ),
    )
    if customer_id is not None:
        text_match_q = text_match_q.filter(
            PrdCustomerProduct.customer_id == customer_id
        )
    text_match = text_match_q.all()

    # 3) PI item 名称字段匹配
    latest_pi_item_sq = (
        db.query(
            PiProformaInvoiceItem.product_id,
            func.max(PiProformaInvoiceItem.id).label("latest_id"),
        )
        .filter(
            PiProformaInvoiceItem.product_id.isnot(None),
            PiProformaInvoiceItem.is_deleted == False,  # noqa: E712
        )
        .group_by(PiProformaInvoiceItem.product_id)
        .subquery()
    )
    pi_name_match_q = (
        db.query(PiProformaInvoiceItem)
        .join(
            latest_pi_item_sq,
            PiProformaInvoiceItem.id == latest_pi_item_sq.c.latest_id,
        )
        .join(PiProformaInvoice, PiProformaInvoice.id == PiProformaInvoiceItem.pi_id)
        .filter(
            or_(
                PiProformaInvoiceItem.detail_desc.ilike(text_kw),
                PiProformaInvoiceItem.customer_model.ilike(text_kw),
                PiProformaInvoiceItem.detail_desc_en.ilike(text_kw),
                PiProformaInvoiceItem.product_short_name.ilike(text_kw),
                PiProformaInvoiceItem.product_short_name_en.ilike(text_kw),
            ),
        )
    )
    if customer_id is not None:
        pi_name_match_q = pi_name_match_q.filter(
            PiProformaInvoice.customer_id == customer_id
        )
    pi_name_match = pi_name_match_q.all()
    latest_name_map = {row.product_id: row for row in pi_name_match}

    # 4) OE 子串匹配
    oe_match: list[PrdCustomerProduct] = []
    if oe_tokens:
        oe_subqs = [
            PrdCustomerProductOE.oe_number.ilike(f"%{tok}%")
            for tok in oe_tokens
            if tok
        ]
        if oe_subqs:
            oe_match_q = (
                db.query(PrdCustomerProduct)
                .join(
                    PrdCustomerProductOE,
                    PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id,
                )
                .filter(
                    PrdCustomerProduct.deleted_at.is_(None),
                    or_(*oe_subqs),
                )
                .distinct()
            )
            if customer_id is not None:
                oe_match_q = oe_match_q.filter(
                    PrdCustomerProduct.customer_id == customer_id
                )
            oe_match = oe_match_q.all()

    # 5) 收集候选 product_id
    candidate_ids: set[int] = set()
    for src_list in [exact_model, text_match, oe_match]:
        for p in src_list:
            candidate_ids.add(p.id)
    candidate_ids |= set(latest_name_map.keys())

    if not candidate_ids:
        return ProductSearchResponse(results=[], total=0)

    # 6) 统一加载候选产品（预加载关联关系避免 N+1）
    products = {
        p.id: p
        for p in db.query(PrdCustomerProduct)
        .options(
            joinedload(PrdCustomerProduct.customer),
            selectinload(PrdCustomerProduct.codes),
            selectinload(PrdCustomerProduct.oes),
        )
        .filter(
            PrdCustomerProduct.id.in_(candidate_ids),
            PrdCustomerProduct.deleted_at.is_(None),
        )
        .all()
    }

    # 7) 对所有候选产品统一加载"最近一次 PI item"作为展示用
    latest_pi_all_sq = (
        db.query(
            PiProformaInvoiceItem.product_id,
            func.max(PiProformaInvoiceItem.id).label("latest_id"),
        )
        .filter(
            PiProformaInvoiceItem.product_id.in_(candidate_ids),
            PiProformaInvoiceItem.is_deleted == False,  # noqa: E712
        )
        .group_by(PiProformaInvoiceItem.product_id)
        .subquery()
    )
    latest_pi_for_display = {
        row.product_id: row
        for row in db.query(PiProformaInvoiceItem)
        .join(
            latest_pi_all_sq,
            PiProformaInvoiceItem.id == latest_pi_all_sq.c.latest_id,
        )
        .filter(PiProformaInvoiceItem.is_deleted == False)  # noqa: E712
        .all()
    }

    # 8) Python 精排
    results: list[tuple[float, PrdCustomerProduct, list[str]]] = []
    for pid, p in products.items():
        score, matched = score_product(
            p, keyword, oe_tokens, latest_pi_for_display.get(pid)
        )
        results.append((score, p, matched))
    results.sort(key=lambda x: (-x[0], x[1].id))
    total = len(results)
    results = results[:limit]

    return ProductSearchResponse(
        results=[
            build_search_item(p, latest_pi_for_display.get(p.id), matched, score)
            for score, p, matched in results
        ],
        total=total,
    )
