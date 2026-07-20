from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
from app.database import get_db
from crud.supplier import (
    create_supplier, get_supplier, get_suppliers, update_supplier, delete_supplier, batch_create_suppliers,
    find_or_create_supplier_by_name
)
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from region_data import get_all_provinces, get_cities_by_province

router = APIRouter(prefix="/api/suppliers", tags=["供应商管理"])


class FindOrCreateSupplierRequest(BaseModel):
    """2026-07-17：线上采购（1688 店铺/微信昵称）按 dept_id+platform+name 查找或创建供应商"""
    supplier_name: str
    dept_id: Optional[str] = "S"
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    platform: Literal['1688', 'wechat', 'offline']   # 必填，缺失返回 422
    shop_link: Optional[str] = None      # 新增：1688 店铺链接
    wechat_id: Optional[str] = None      # 新增：微信号
    wechat_nickname: Optional[str] = None  # 新增：微信昵称
    is_dropship: Optional[bool] = None   # 新增：是否代发


class FindOrCreateSupplierResponse(BaseModel):
    id: int
    supplier_name: str
    supplier_code: Optional[str] = None
    created: bool  # True=新建，False=复用现有


@router.post("/find-or-create", response_model=FindOrCreateSupplierResponse)
def find_or_create_supplier_api(
    payload: FindOrCreateSupplierRequest,
    db: Session = Depends(get_db)
):
    """2026-07-17：按 dept_id+platform+name 查找或创建供应商（用于线上采购自动建立 supplier_id）

    校验失败统一返回 422（HTTPException），避免 FastAPI 默认 500 误判。
    """
    # supplier_name 纯空白拦截（None.strip() 会抛 AttributeError，必须先判 None）
    if not payload.supplier_name or not payload.supplier_name.strip():
        raise HTTPException(status_code=422, detail="supplier_name 不能为空")

    dept_id = payload.dept_id or "S"

    try:
        result = find_or_create_supplier_by_name(
            db,
            supplier_name=payload.supplier_name,
            platform=payload.platform,  # Literal 必填，路由层无需二次校验
            dept_id=dept_id,
            contact_person=payload.contact_person,
            phone=payload.phone,
            address=payload.address,
            shop_link=payload.shop_link,
            wechat_id=payload.wechat_id,
            wechat_nickname=payload.wechat_nickname,
            is_dropship=payload.is_dropship,
        )
    except ValueError as e:
        # 平台校验 / 1688 shop_link 缺失等业务错误统一 422
        raise HTTPException(status_code=422, detail=str(e))

    if result is None:
        raise HTTPException(status_code=500, detail="创建供应商失败")

    new_supplier, created = result
    return FindOrCreateSupplierResponse(
        id=new_supplier.id,
        supplier_name=new_supplier.supplier_name,
        supplier_code=new_supplier.supplier_code,
        created=created,
    )

@router.post("/", response_model=SupplierResponse)
def create_supplier_api(supplier: SupplierCreate, dept_id: str = "S", db: Session = Depends(get_db)):
    try:
        return create_supplier(db, supplier, dept_id)
    except ValueError as e:
        # 平台必填字段校验失败 → 422
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/", response_model=list[SupplierResponse])
def read_suppliers(skip: int = 0, limit: int = 100, keyword: Optional[str] = None, db: Session = Depends(get_db)):
    return get_suppliers(db, skip=skip, limit=limit, keyword=keyword)

@router.get("/provinces")
def get_provinces():
    return get_all_provinces()

@router.get("/cities/{province}")
def get_cities(province: str):
    return get_cities_by_province(province)

@router.get("/{supplier_id}", response_model=SupplierResponse)
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return db_supplier

@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier_api(supplier_id: int, supplier: SupplierUpdate, db: Session = Depends(get_db)):
    try:
        db_supplier = update_supplier(db, supplier_id, supplier)
    except ValueError as e:
        # 平台变更锁定 / 1688 shop_link 缺失等业务错误统一 422
        raise HTTPException(status_code=422, detail=str(e))
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return db_supplier

@router.delete("/{supplier_id}")
def delete_supplier_api(supplier_id: int, db: Session = Depends(get_db)):
    success = delete_supplier(db, supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return {"message": "供应商已删除"}

@router.post("/batch")
def batch_create_suppliers_api(suppliers: dict, dept_id: str = "S", db: Session = Depends(get_db)):
    supplier_list = suppliers.get("suppliers", [])
    if not supplier_list:
        raise HTTPException(status_code=400, detail="供应商列表不能为空")
    
    result = batch_create_suppliers(db, supplier_list, dept_id)
    return result