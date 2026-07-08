# -*- coding: utf-8 -*-
"""
订单总表 BFF 层 Schema 定义

包含订单列表、订单详情等相关 Pydantic 模型
OrderDetailItemSchema 共 41 列，按 A-F 组排列，与 Excel 订单管理总表完全对齐
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class OrderListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pi_no: str
    customer_id: int
    customer_name: str
    customer_country: str = ""
    created_at: Optional[str] = None
    item_count: int = 0
    total_amount: float = 0
    status: int = 1
    status_label: str = ""
    paid_amount: float = 0
    unpaid_amount: float = 0
    payment_progress: float = 0
    payment_status: str = "未付款"
    stock_remaining: float = 0
    storage_status: str = ""


class OrderDetailItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pi_id: int
    product_id: Optional[int] = None

    # ========== A组：基础信息 (列1-9) ==========
    order_date: Optional[str] = None
    pi_no: str = ""
    product_code: str = ""
    oe_number: str = ""
    remark: str = ""
    product_name: str = ""
    product_name_en: str = ""
    image_url: str = ""
    customer_model: str = ""
    product_feature: str = ""
    product_acquires: str = ""
    product_color: str = ""

    # ========== B组：价格财务 (列10-21) ==========
    quantity: float = 0
    unit_price: float = 0
    total_amount: float = 0
    latest_customer_reply: str = ""
    customer_prepayment: float = 0
    remaining_payment: float = 0
    estimated_usd_price: float = 0
    estimated_margin: float = 0
    purchase_price: float = 0
    shipping_fee: float = 0
    misc_fee: float = 0
    labeling_fee: float = 0
    tax_fee: float = 0
    freight: float = 0
    total_cost: float = 0

    # ========== C组：供应商采购 (列22-27) ==========
    factory_name: str = ""
    shop_url: str = ""
    delivery_date: Optional[str] = None
    storage_status: str = ""
    factory_deposit: float = 0
    factory_balance: float = 0

    # ========== D组：物流入库 (列28-30) ==========
    stock_in_action: str = ""
    stock_in_quantity: float = 0
    packaging: str = ""

    # ========== E组：产品细节 (列31-39) ==========
    purchase_option_name: str = ""
    product_detail: str = ""
    company_code: str = ""  # 我司产编号 S.NO.（默认等于 customer_model）
    factory_code: str = ""
    carton_size: str = ""
    pack_spec: str = ""
    carton_count: int = 0
    estimated_volume: float = 0
    carton_gross_weight: float = 0
    total_weight: float = 0

    # ========== F组：其他属性 (列40-41) ==========
    brand: str = ""
    invoice_status: str = ""


class OrderListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    list: List[OrderListItemSchema]
    total: int
    page: int
    page_size: int


class OrderDetailResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order: OrderListItemSchema
    items: List[OrderDetailItemSchema]
