"""BFF (Backend for Frontend) 聚合接口
为 Vue 前端提供订单管理模块的聚合数据接口，
减少前端多接口调用，提升页面加载速度。
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.database import get_db
from models.customer import CrmCustomer
from models.customer_product import PrdCustomerProduct
from models.product_category import PrdProductCategory
from models.pi import PiProformaInvoice, PiProformaInvoiceItem, PiPaymentStage
from models.purchase import Po1688Purchase
from schemas.bff_order import (
    OrderListItemSchema,
    OrderDetailItemSchema,
    OrderListResponseSchema,
    OrderDetailResponseSchema,
)

router = APIRouter(prefix="/bff", tags=["bff"])

STATUS_MAP = {
    0: "已取消",
    1: "待处理",
    2: "处理中",
    3: "已完成",
}

_FALLBACK_CATEGORY_NAMES = {
    "C": "汽配件", "F": "办公家具", "B": "百货类",
    "C01": "发动机", "C02": "曲轴", "C03": "刹车片", "C09": "杂项",
    "F01": "椅子类", "F02": "桌子类", "F88": "工程定制",
    "B00": "百货类",
}

_FALLBACK_CATEGORY_PARENTS = {
    "C01": "C", "C02": "C", "C03": "C", "C09": "C",
    "F01": "F", "F02": "F", "F88": "F",
    "B00": "B",
}


def _status_label(status_val: Optional[int]) -> str:
    """将状态数值转换为中文标签。"""
    if status_val is None:
        return "未知"
    return STATUS_MAP.get(status_val, f"状态{status_val}")


def _to_float(val: Any) -> float:
    """安全转换为 float，失败返回 0.0。"""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# 后端静态资源实际可访问的域名（生产环境）
_ASSET_BASE = "https://piapi.wakabashia.tj.cn"


def _absolute_url(request: Request, path: str) -> str:
    """把后端静态相对路径 /images/xxx 升级成绝对 URL，
    避免部署到不同域名（前端 piapi/后端 pidatabase）时浏览器找不到资源。
    """
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://") or path.startswith("data:"):
        return path
    if not path.startswith("/"):
        return path
    return f"{_ASSET_BASE}{path}"


def _to_str(val: Any) -> str:
    """安全转换为 str，None 返回空字符串。"""
    if val is None:
        return ""
    return str(val)


def _datetime_to_iso(dt: Any) -> Optional[str]:
    """将 datetime 转换为 ISO 格式字符串。"""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _calc_payment_status(progress: float) -> str:
    """根据付款进度计算付款状态文字。"""
    if progress <= 0:
        return "未付款"
    elif progress >= 100:
        return "已付清"
    else:
        return "部分付款"


def _calc_storage_status(items: List[PiProformaInvoiceItem]) -> str:
    """根据订单明细的入库状态计算整体入库状态。"""
    if not items:
        return "未入库"
    statuses = set()
    for item in items:
        if item.storage_status:
            statuses.add(item.storage_status)
        else:
            statuses.add("未入库")
    if "已入库" in statuses and len(statuses) == 1:
        return "已入库"
    if "未入库" in statuses and len(statuses) == 1:
        return "未入库"
    return "部分入库"


def _parse_date(date_str: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    """解析 ISO 格式日期字符串，可选设置为当天结束时间。"""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt
    except (ValueError, TypeError):
        return None


def _apply_order_filters(
    query,
    customer_id: Optional[int] = None,
    status: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """向订单查询应用客户、状态、日期范围筛选条件。"""
    if customer_id:
        query = query.filter(PiProformaInvoice.customer_id == customer_id)
    if status is not None:
        query = query.filter(PiProformaInvoice.status == status)
    dt_from = _parse_date(date_from)
    if dt_from:
        query = query.filter(PiProformaInvoice.created_at >= dt_from)
    dt_to = _parse_date(date_to, end_of_day=True)
    if dt_to:
        query = query.filter(PiProformaInvoice.created_at <= dt_to)
    return query


def _build_order_list_item(
    order: PiProformaInvoice,
    customer_name: str,
    customer_country: str,
    item_count: int,
    paid_amount: float,
    total_qty: float,
    stocked_qty: float,
    storage_status: str,
) -> OrderListItemSchema:
    total_amount = _to_float(order.total_amount)
    unpaid_amount = max(total_amount - paid_amount, 0.0)
    payment_progress = (paid_amount / total_amount * 100) if total_amount > 0 else 0.0
    payment_progress = min(payment_progress, 100.0)
    payment_status = _calc_payment_status(payment_progress)
    stock_remaining = max(total_qty - stocked_qty, 0.0)

    return OrderListItemSchema(
        id=order.id or 0,
        pi_no=order.pi_no or "",
        customer_id=order.customer_id or 0,
        customer_name=customer_name,
        customer_country=customer_country,
        created_at=_datetime_to_iso(order.created_at),
        item_count=item_count,
        total_amount=total_amount,
        status=order.status or 1,
        status_label=_status_label(order.status),
        paid_amount=round(paid_amount, 2),
        unpaid_amount=round(unpaid_amount, 2),
        payment_progress=round(payment_progress, 2),
        payment_status=payment_status,
        stock_remaining=round(stock_remaining, 2),
        storage_status=storage_status,
    )


@router.get("/orders/dashboard")
def get_order_dashboard(
    status: Optional[int] = Query(None, description="订单状态筛选"),
    customer_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """订单仪表盘聚合接口"""
    if date_from and _parse_date(date_from) is None:
        return {"code": 400, "message": "日期格式错误", "data": None}
    if date_to and _parse_date(date_to) is None:
        return {"code": 400, "message": "日期格式错误", "data": None}

    query = db.query(PiProformaInvoice)
    query = _apply_order_filters(query, customer_id, status, date_from, date_to)

    total_count = query.count()

    total_amount = _to_float(
        query.with_entities(func.sum(PiProformaInvoice.total_amount)).scalar()
    )

    status_query = db.query(PiProformaInvoice)
    status_query = _apply_order_filters(status_query, customer_id, None, date_from, date_to)
    status_rows = status_query.with_entities(
        PiProformaInvoice.status, func.count(PiProformaInvoice.id)
    ).group_by(PiProformaInvoice.status).all()
    status_stats: Dict[str, int] = {}
    for status_val, count in status_rows:
        status_stats[_status_label(status_val)] = count

    pi_ids = [o.id for o in query.all() if o.id]
    total_paid = 0.0
    if pi_ids:
        paid_result = db.query(
            func.sum(PiPaymentStage.amount)
        ).filter(
            PiPaymentStage.pi_id.in_(pi_ids),
            PiPaymentStage.status == 2,
        ).scalar()
        total_paid = _to_float(paid_result)

    total_unpaid = max(total_amount - total_paid, 0.0)
    payment_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0.0

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
            "status_stats": status_stats,
            "payment_stats": {
                "total_paid": round(total_paid, 2),
                "total_unpaid": round(total_unpaid, 2),
                "payment_rate": round(payment_rate, 2),
            },
        }
    }


@router.get("/orders")
def get_orders_bff(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[int] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = Query(None, description="搜索PI号/客户名"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """订单列表 BFF 接口（15列聚合）"""
    if date_from and _parse_date(date_from) is None:
        return {"code": 400, "message": "日期格式错误", "data": None}
    if date_to and _parse_date(date_to) is None:
        return {"code": 400, "message": "日期格式错误", "data": None}

    query = db.query(PiProformaInvoice)
    query = _apply_order_filters(query, customer_id, status, date_from, date_to)

    if search:
        like = f"%{search}%"
        query = query.outerjoin(CrmCustomer, PiProformaInvoice.customer_id == CrmCustomer.id).filter(
            (PiProformaInvoice.pi_no.like(like)) | (CrmCustomer.customer_name.like(like))
        )

    total = query.count()
    orders = (
        query.order_by(PiProformaInvoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    order_ids = [o.id for o in orders if o.id]
    customer_ids = [o.customer_id for o in orders if o.customer_id]

    customer_map: Dict[int, str] = {}
    customer_country_map: Dict[int, str] = {}
    if customer_ids:
        customers = db.query(CrmCustomer).filter(CrmCustomer.id.in_(customer_ids)).all()
        customer_map = {c.id: c.customer_name for c in customers if c.id}
        customer_country_map = {c.id: (c.country or "") for c in customers if c.id}

    item_count_map: Dict[int, int] = {}
    paid_amount_map: Dict[int, float] = {}
    items_map: Dict[int, List[PiProformaInvoiceItem]] = {}

    if order_ids:
        item_counts = db.query(
            PiProformaInvoiceItem.pi_id,
            func.count(PiProformaInvoiceItem.id)
        ).filter(
            PiProformaInvoiceItem.pi_id.in_(order_ids),
            PiProformaInvoiceItem.is_deleted == False,
        ).group_by(PiProformaInvoiceItem.pi_id).all()
        for pi_id, count in item_counts:
            item_count_map[pi_id] = count

        paid_amounts = db.query(
            PiPaymentStage.pi_id,
            func.sum(PiPaymentStage.amount)
        ).filter(
            PiPaymentStage.pi_id.in_(order_ids),
            PiPaymentStage.status == 2,
        ).group_by(PiPaymentStage.pi_id).all()
        for pi_id, amount in paid_amounts:
            paid_amount_map[pi_id] = _to_float(amount)

        all_items = db.query(PiProformaInvoiceItem).filter(
            PiProformaInvoiceItem.pi_id.in_(order_ids),
            PiProformaInvoiceItem.is_deleted == False,
        ).all()
        for item in all_items:
            if item.pi_id not in items_map:
                items_map[item.pi_id] = []
            items_map[item.pi_id].append(item)

    result = []
    for o in orders:
        oid = o.id or 0
        items = items_map.get(oid, [])

        total_qty = 0.0
        stocked_qty = 0.0
        for item in items:
            total_qty += _to_float(item.quantity)
            stocked_qty += _to_float(item.stocked_qty)

        storage_status = _calc_storage_status(items)

        order_item = _build_order_list_item(
            order=o,
            customer_name=customer_map.get(o.customer_id or 0, ""),
            customer_country=customer_country_map.get(o.customer_id or 0, ""),
            item_count=item_count_map.get(oid, 0),
            paid_amount=paid_amount_map.get(oid, 0.0),
            total_qty=total_qty,
            stocked_qty=stocked_qty,
            storage_status=storage_status,
        )
        result.append(order_item)

    response_data = OrderListResponseSchema(
        list=result,
        total=total,
        page=page,
        page_size=page_size,
    )

    return {
        "code": 200,
        "message": "success",
        "data": response_data.model_dump(),
    }


def _build_order_detail_item(
    item: PiProformaInvoiceItem,
    pi_no: str,
    order_date: Optional[str],
    latest_1688: Any = None,
    request: Optional[Request] = None,
    customer_product_map: Optional[Dict[int, PrdCustomerProduct]] = None,
    category_map: Optional[Dict[str, PrdProductCategory]] = None,
) -> OrderDetailItemSchema:
    carton_size = ""
    if item.carton_length_cm or item.carton_width_cm or item.carton_height_cm:
        parts = []
        if item.carton_length_cm:
            parts.append(str(item.carton_length_cm))
        if item.carton_width_cm:
            parts.append(str(item.carton_width_cm))
        if item.carton_height_cm:
            parts.append(str(item.carton_height_cm))
        carton_size = "x".join(parts) if parts else ""
    elif item.carton_size:
        carton_size = _to_str(item.carton_size)

    estimated_volume = 0.0
    if item.carton_length_cm and item.carton_width_cm and item.carton_height_cm and item.carton_count:
        try:
            estimated_volume = (
                float(item.carton_length_cm) *
                float(item.carton_width_cm) *
                float(item.carton_height_cm) *
                float(item.carton_count)
            ) / 1000000.0
        except (ValueError, TypeError):
            estimated_volume = 0.0

    total_weight = 0.0
    if item.carton_gross_weight and item.carton_count:
        try:
            total_weight = float(item.carton_gross_weight) * float(item.carton_count)
        except (ValueError, TypeError):
            total_weight = 0.0

    purchase_price = _to_float(item.purchase_price)
    quantity = _to_float(item.quantity)
    unit_price = _to_float(item.unit_price)
    shipping_fee = _to_float(item.shipping_fee)
    misc_fee = _to_float(item.misc_fee)
    # 直接取原值，仅在 None 时使用默认值（不做假值判断，避免 0 被误判）
    _raw_exchange = getattr(item, "exchange_rate", None)
    _raw_profit = getattr(item, "profit_margin", None)
    exchange_rate = _to_float(_raw_exchange) if _raw_exchange is not None else 6.8
    profit_margin = _to_float(_raw_profit) if _raw_profit is not None else 25.0
    purchase_currency = _to_str(getattr(item, "purchase_currency", "RMB")).upper() or "RMB"
    factor = 1 + profit_margin / 100.0
    if purchase_currency == "USD":
        estimated_usd_price = round(purchase_price * factor, 2)
        purchase_cost_usd = purchase_price * quantity + shipping_fee + misc_fee
    else:
        estimated_usd_price = round(purchase_price * factor / exchange_rate, 2) if exchange_rate else 0.0
        purchase_cost_usd = (purchase_price * quantity + shipping_fee + misc_fee) / exchange_rate if exchange_rate else 0.0
    revenue_usd = unit_price * quantity
    estimated_margin = round(((revenue_usd - purchase_cost_usd) / revenue_usd) * 100, 2) if revenue_usd else 0.0

    category_id = None
    category_name = None
    category_parent_name = None
    customer_product = None
    if item.product_id and customer_product_map:
        customer_product = customer_product_map.get(item.product_id)
    if customer_product and customer_product.category_id:
        category_id = customer_product.category_id
    elif item.temp_category_id:
        category_id = item.temp_category_id
    if category_id:
        category = category_map.get(category_id) if category_map else None
        category_name = category.name if category else _FALLBACK_CATEGORY_NAMES.get(category_id)
        parent_code = category.parent_id if category else _FALLBACK_CATEGORY_PARENTS.get(category_id)
        if parent_code:
            parent_category = category_map.get(parent_code) if category_map else None
            category_parent_name = parent_category.name if parent_category else _FALLBACK_CATEGORY_NAMES.get(parent_code)

    return OrderDetailItemSchema(
        id=item.id or 0,
        pi_id=item.pi_id or 0,
        product_id=item.product_id,
        order_date=order_date,
        pi_no=pi_no,
        product_code=_to_str(item.customer_code),
        oe_number=_to_str(item.oe_number),
        remark=_to_str(item.remark),
        product_name=_to_str(item.detail_desc),
        product_name_en=_to_str(item.detail_desc_en),
        product_short_name=_to_str(item.product_short_name),
        product_short_name_en=_to_str(item.product_short_name_en),
        image_url=_absolute_url(request, _to_str(item.temp_image)) if request else _to_str(item.temp_image),
        customer_model=_to_str(item.customer_model),
        product_feature=_to_str(item.product_feature),
        product_acquires=_to_str(item.product_acquires),
        product_color=_to_str(item.product_color),
        category_id=category_id,
        category_name=category_name,
        category_parent_name=category_parent_name,
        quantity=_to_float(item.quantity),
        unit_price=_to_float(item.unit_price),
        total_amount=_to_float(item.total_price),
        latest_customer_reply="",
        customer_prepayment=_to_float(item.customer_prepayment),
        remaining_payment=_to_float(item.remaining_payment),
        estimated_usd_price=estimated_usd_price,
        estimated_margin=estimated_margin,
        purchase_price=purchase_price,
        shipping_fee=_to_float(item.shipping_fee),
        misc_fee=_to_float(item.misc_fee),
        labeling_fee=_to_float(latest_1688.labeling_fee) if latest_1688 else 0.0,
        tax_fee=_to_float(latest_1688.tax_fee) if latest_1688 else 0.0,
        freight=_to_float(latest_1688.freight) if latest_1688 else 0.0,
        total_cost=round(purchase_price * quantity + shipping_fee + misc_fee, 2),
        factory_name=_to_str(item.supplier_name),
        shop_url=_to_str(item.shop_url),
        delivery_date=_datetime_to_iso(item.delivery_date),
        storage_status=_to_str(item.storage_status),
        factory_deposit=_to_float(item.factory_deposit),
        factory_balance=_to_float(item.factory_balance),
        stock_in_action="",
        stock_in_quantity=_to_float(item.stocked_qty),
        packaging=_to_str(item.packaging),
        purchase_option_name=_to_str(item.purchase_option_name),
        product_detail=_to_str(item.product_detail),
        company_code=_to_str(item.company_code),
        profit_margin=profit_margin if profit_margin is not None else None,
        exchange_rate=exchange_rate if exchange_rate is not None else None,
        factory_code=_to_str(item.factory_code),
        carton_size=carton_size,
        pack_spec=_to_str(item.pack_spec),
        carton_count=item.carton_count or 0,
        estimated_volume=round(estimated_volume, 4),
        carton_gross_weight=_to_float(item.carton_gross_weight),
        total_weight=round(total_weight, 4),
        inbound_records=getattr(item, "inbound_records", None) or [],
        brand=_to_str(item.brand),
        invoice_status=_to_str(item.invoice_status),
    )


@router.get("/orders/{order_id}/full-detail")
def get_order_full_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """订单详情 BFF 接口（41列产品明细）"""
    order = db.query(PiProformaInvoice).filter(PiProformaInvoice.id == order_id).first()
    if not order:
        return {"code": 404, "message": "订单不存在", "data": None}

    customer_name = ""
    customer_country = ""
    if order.customer_id:
        cust = db.query(CrmCustomer).filter(CrmCustomer.id == order.customer_id).first()
        if cust:
            customer_name = cust.customer_name
            customer_country = cust.country or ""

    items = db.query(PiProformaInvoiceItem).filter(
        PiProformaInvoiceItem.pi_id == order.id,
        PiProformaInvoiceItem.is_deleted == False,
    ).order_by(PiProformaInvoiceItem.id.asc()).all()

    item_count = len(items)

    paid_amount = 0.0
    paid_result = db.query(
        func.sum(PiPaymentStage.amount)
    ).filter(
        PiPaymentStage.pi_id == order.id,
        PiPaymentStage.status == 2,
    ).scalar()
    paid_amount = _to_float(paid_result)

    total_qty = 0.0
    stocked_qty = 0.0
    for item in items:
        total_qty += _to_float(item.quantity)
        stocked_qty += _to_float(item.stocked_qty)

    storage_status = _calc_storage_status(items)

    order_info = _build_order_list_item(
        order=order,
        customer_name=customer_name,
        customer_country=customer_country,
        item_count=item_count,
        paid_amount=paid_amount,
        total_qty=total_qty,
        stocked_qty=stocked_qty,
        storage_status=storage_status,
    )

    order_date = _datetime_to_iso(order.created_at)
    pi_no = order.pi_no or ""

    # 批量查询每个产品的最新 1688 采购记录
    product_ids = [item.product_id for item in items if item.product_id]
    latest_1688_map: Dict[int, Any] = {}
    if product_ids:
        # 取每个 product_id 按时间倒序第一条
        subq = (
            db.query(
                Po1688Purchase.product_id,
                func.max(Po1688Purchase.created_at).label("max_created"),
            )
            .filter(Po1688Purchase.product_id.in_(product_ids))
            .group_by(Po1688Purchase.product_id)
            .subquery()
        )
        latest_records = (
            db.query(Po1688Purchase)
            .join(
                subq,
                (Po1688Purchase.product_id == subq.c.product_id)
                & (Po1688Purchase.created_at == subq.c.max_created),
            )
            .all()
        )
        latest_1688_map = {r.product_id: r for r in latest_records}

    customer_product_map: Dict[int, PrdCustomerProduct] = {}
    category_map: Dict[str, PrdProductCategory] = {}
    if product_ids:
        customer_products = db.query(PrdCustomerProduct).filter(
            PrdCustomerProduct.id.in_(product_ids)
        ).all()
        customer_product_map = {p.id: p for p in customer_products}
        category_codes = [p.category_id for p in customer_products if p.category_id]
        category_codes.extend([item.temp_category_id for item in items if item.temp_category_id])
        if category_codes:
            categories = db.query(PrdProductCategory).filter(
                PrdProductCategory.code.in_(category_codes + list(_FALLBACK_CATEGORY_PARENTS.values()))
            ).all()
            category_map = {c.code: c for c in categories}

    detail_items = [
        _build_order_detail_item(
            item, pi_no, order_date,
            latest_1688=latest_1688_map.get(item.product_id),
            request=request,
            customer_product_map=customer_product_map,
            category_map=category_map,
        )
        for item in items
    ]

    response_data = OrderDetailResponseSchema(
        order=order_info,
        items=detail_items,
    )

    return {
        "code": 200,
        "message": "success",
        "data": response_data.model_dump(),
    }
