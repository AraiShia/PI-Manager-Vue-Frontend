from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from crud.purchase import (
    create_purchase_order, create_grouped_purchase_orders, get_purchase_order, get_purchase_orders,
    update_purchase_status, create_1688_purchase, get_1688_purchases,
    update_purchase_order, get_purchase_orders_by_supplier,
    get_product_latest_purchase, create_1688_purchase_batch
)
from schemas.purchase import (
    PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderDetailResponse, PurchaseOrderUpdate,
    Po1688PurchaseItem, Po1688PurchaseBatchCreate
)
from models.purchase import Po1688Purchase
from models import SupSupplier

router = APIRouter(prefix="/api/purchase-orders", tags=["采购管理"])
@router.post("", response_model=PurchaseOrderResponse, include_in_schema=False)
@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order_api(purchase: PurchaseOrderCreate, db: Session = Depends(get_db)):
    try:
        return create_purchase_order(db, purchase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[PurchaseOrderResponse], include_in_schema=False)
@router.get("/", response_model=list[PurchaseOrderResponse])
def read_purchase_orders(skip: int = 0, limit: int = 100, status: int = None, pi_id: int = None, db: Session = Depends(get_db)):
    """[2026-06-23 修复] 列表中手动 join PI 与供应商，把 pi_no / supplier_name 填进响应，
    前端采购管理 Tab 才能展示（否则两列永远是空字符串，看起来像"无采购单"）"""
    from models import PiProformaInvoice, SupSupplier
    pos = get_purchase_orders(db, skip=skip, limit=limit, status=status, pi_id=pi_id)
    if not pos:
        return []
    # 批量取 PI 号、供应商名
    pi_ids = {po.pi_id for po in pos if po.pi_id}
    sup_ids = {po.supplier_id for po in pos if po.supplier_id}
    pi_no_map = {}
    if pi_ids:
        for pi in db.query(PiProformaInvoice).filter(PiProformaInvoice.id.in_(pi_ids)).all():
            pi_no_map[pi.id] = pi.pi_no
    sup_name_map = {}
    if sup_ids:
        for s in db.query(SupSupplier).filter(SupSupplier.id.in_(sup_ids)).all():
            sup_name_map[s.id] = s.supplier_name
    result = []
    for po in pos:
        result.append({
            "id": po.id,
            "po_no": po.po_no,
            "dept_id": po.dept_id,
            "pi_id": po.pi_id,
            "supplier_id": po.supplier_id,
            "pi_no": pi_no_map.get(po.pi_id, ""),
            "supplier_name": sup_name_map.get(po.supplier_id, ""),
            "total_amount": po.total_amount,
            "status": po.status,
            "created_at": po.created_at,
        })
    return result

@router.get("/{po_id}", response_model=PurchaseOrderDetailResponse)
def read_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """[2026-06-17 计划] 返回采购单详情(包含 items, 每个 item 含 snapshot 字段)"""
    db_po = get_purchase_order(db, po_id)
    if db_po is None:
        raise HTTPException(status_code=404, detail="采购单不存在")
    # 触发 lazy load items
    _ = db_po.items
    return db_po

@router.put("/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order_api(po_id: int, purchase_update: PurchaseOrderUpdate, db: Session = Depends(get_db)):
    try:
        db_po = update_purchase_order(db, po_id, purchase_update)
        if db_po is None:
            raise HTTPException(status_code=404, detail="采购单不存在")
        return db_po
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{po_id}/confirm")
def confirm_purchase(po_id: int, db: Session = Depends(get_db)):
    db_po = update_purchase_status(db, po_id, 2)
    if db_po is None:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return {"message": "采购已确认", "purchase_order": db_po}

@router.post("/{po_id}/inbound")
def inbound_purchase(po_id: int, db: Session = Depends(get_db)):
    db_po = update_purchase_status(db, po_id, 3)
    if db_po is None:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return {"message": "已入库", "purchase_order": db_po}

@router.post("/1688")
def create_1688_purchase_api(purchase_data: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """2026-07-20：1688 线上采购（同时记录 1688 采购明细）

    业务校验（2026-07-20 补充）：
    - supplier_id 与 supplier_name 均缺失/空白 → 422
    - supplier_id 关联时校验：供应商存在、dept_id 一致、platform 非 NULL、platform 一致
    - 所有 CRUD 层 ValueError 在路由层统一转换为 HTTPException(422)
    """
    # 兼容 dict 与 pydantic
    if hasattr(purchase_data, "model_dump"):
        data = purchase_data.model_dump()
    elif hasattr(purchase_data, "dict"):
        data = purchase_data.dict()
    else:
        data = dict(purchase_data)

    # ── 业务校验层 ───────────────────────────────────────────────
    # 1. supplier_name 空白校验（None.strip() 会抛 AttributeError，必须先判 None）
    supplier_name_raw = data.get("supplier_name")
    has_supplier_name = bool(supplier_name_raw and str(supplier_name_raw).strip())

    if not data.get("supplier_id") and not has_supplier_name:
        raise HTTPException(
            status_code=422,
            detail="supplier_id 或 supplier_name（非空）至少填写一个"
        )

    # 2. supplier_id 关联时校验供应商/部门/平台一致性
    supplier_id = data.get("supplier_id")
    dept_id = data.get("dept_id") or "S"
    platform = data.get("platform")  # PurchaseOrderCreate 当前无此字段，兼容 dict 读取

    if supplier_id:
        supplier = db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=422, detail="供应商不存在")
        # 2.1 部门一致性
        if supplier.dept_id != dept_id:
            msg = f'所选供应商部门为 {supplier.dept_id}，与本次采购部门 {dept_id} 不一致，请选择本部门供应商或通过"新建供应商"创建'
            raise HTTPException(status_code=422, detail=msg)
        # 2.2 NULL 平台供应商禁止用于线上采购
        if supplier.platform is None:
            msg = f'所选供应商（{supplier.supplier_name}）尚未分配平台，无法关联到线上采购。请先在"供应商管理"中为该供应商设置平台类型。'
            raise HTTPException(status_code=422, detail=msg)
        # 2.3 平台一致性
        if platform and supplier.platform != platform:
            msg = f'所选供应商平台为 {supplier.platform}，与本次采购平台 {platform} 不一致，请重新选择或使用"新建供应商"流程'
            raise HTTPException(status_code=422, detail=msg)
    # ── 业务校验层 end ─────────────────────────────────────────

    # 1) 1688 采购明细：从完整 items 中提取 1688 维度字段
    created_records: list = []
    src_items = data.get("items") or []
    if src_items:
        batch_items = []
        for it in src_items:
            batch_items.append(Po1688PurchaseItem(
                product_id=it.get("product_id"),
                supplier_name=it.get("supplier_name") or data.get("supplier_name"),
                product_url=it.get("link") or it.get("product_url"),
                product_remark=it.get("remark"),
                color=it.get("color"),
                invoice_type=it.get("invoice_type"),
                labeling_fee=it.get("labeling_fee"),
                shipping_fee=it.get("shipping_fee"),
                shipping_method=it.get("shipping_method"),
                carton_count=it.get("carton_count"),
                freight=it.get("freight"),
                unit_price=it.get("unit_price"),
                tax_fee=it.get("tax_fee"),
                payment_method=it.get("payment_method"),
                gross_weight=it.get("gross_weight"),
            ))
        batch = Po1688PurchaseBatchCreate(
            dept_id=dept_id,
            po_id=data.get("po_id"),
            pi_id=data.get("pi_id"),
            screenshot=data.get("screenshot"),
            remark=data.get("remark"),
            items=batch_items,
        )
        try:
            created_records = create_1688_purchase_batch(db, batch)
        except ValueError as e:
            # CRUD 层业务错误统一转 422
            raise HTTPException(status_code=422, detail=str(e))

    # 2) 按 supplier_id 分组生成采购单
    try:
        payload = PurchaseOrderCreate(**data)
        purchase_orders = create_grouped_purchase_orders(db, payload)
    except ValueError as e:
        # CRUD 层业务错误（supplier 不存在 / PI 不存在等）→ 422
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "success": True,
        "purchase_orders": purchase_orders,
        "records": created_records,
    }

@router.get("/1688/recent-urls")
def read_recent_1688_urls(product_id: int, limit: int = 5, db: Session = Depends(get_db)):
    rows = (
        db.query(Po1688Purchase.product_url)
        .filter(Po1688Purchase.product_id == product_id)
        .filter(Po1688Purchase.product_url.isnot(None))
        .filter(Po1688Purchase.product_url != "")
        .order_by(Po1688Purchase.created_at.desc(), Po1688Purchase.id.desc())
        .limit(max(limit * 3, limit))
        .all()
    )
    urls = []
    seen = set()
    for (url,) in rows:
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= limit:
            break
    return {"code": 200, "message": "success", "data": {"urls": urls}}

@router.get("/1688")
def read_1688_purchases(pi_id: int = None, product_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_1688_purchases(db, pi_id=pi_id, product_id=product_id, skip=skip, limit=limit)

@router.get("/by-supplier/{supplier_id}", response_model=list[PurchaseOrderResponse])
def read_purchases_by_supplier(supplier_id: int, db: Session = Depends(get_db)):
    return get_purchase_orders_by_supplier(db, supplier_id)

@router.get("/product/{product_id}/latest")
def read_product_latest_purchase(product_id: int, db: Session = Depends(get_db)):
    """获取产品最近一次采购记录（包含费用和发票信息）"""
    record = get_product_latest_purchase(db, product_id)
    # 没有历史采购记录是正常业务状态，不应被前端响应拦截器判定为请求失败。
    return {"success": True, "record": record}
