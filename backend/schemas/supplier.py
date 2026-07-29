from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class SupplierBase(BaseModel):
    dept_id: Optional[str] = "S"
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = ""
    region: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    city_code: Optional[str] = None

class SupplierCreate(BaseModel):
    supplier_name: str
    province: Optional[str] = None
    city: Optional[str] = None
    city_code: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    # 平台分类字段（包含 online, offline, 1688, wechat）
    platform: Optional[Literal['online', 'offline', '1688', 'wechat']] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = False
    # 业务扩展字段（采购方式与微信）
    supply_mode: Optional[str] = None
    supplier_wechat: Optional[str] = None

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    source_location: Optional[str] = None
    invoice_type: Optional[int] = None
    tax_rate: Optional[float] = None
    supply_cycle_days: Optional[int] = None
    return_policy: Optional[str] = None
    payment_terms: Optional[str] = None
    status: Optional[int] = None
    # 平台分类字段（包含 online, offline, 1688, wechat）
    platform: Optional[Literal['online', 'offline', '1688', 'wechat']] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None
    # 业务扩展字段（采购方式与微信）
    supply_mode: Optional[str] = None
    supplier_wechat: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int
    status: Optional[int] = 1
    created_at: Optional[datetime] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    # 平台分类字段（2026-07-17 新增，前端读取并回填表单）
    platform: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None
    # 业务扩展字段（采购方式与微信）
    supply_mode: Optional[str] = None
    supplier_wechat: Optional[str] = None

    class Config:
        from_attributes = True


