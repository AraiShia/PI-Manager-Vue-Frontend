# -*- coding: utf-8 -*-
"""
产品-供应商-URL 关联模型

存储 prd_customer_product 与 sup_supplier 之间的 1688 产品链接关系。
唯一索引：(product_id, supplier_id, url)
supplier_id 可为 NULL（历史导入数据只读）。
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func,
)
from app.database import Base


class PrdProductSupplierUrl(Base):
    __tablename__ = "prd_product_supplier_url"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    product_id    = Column(Integer, ForeignKey("prd_customer_product.id"), nullable=False)
    supplier_id   = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
    supplier_name = Column(String(200), nullable=False)
    url           = Column(String(500), nullable=False)
    display_name  = Column(String(100), nullable=True)
    is_default    = Column(Boolean, default=False)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", "url", name="ux_product_supplier_url"),
        Index("ix_product_supplier_url_supplier", "supplier_id"),
        Index("ix_product_supplier_url_product", "product_id"),
    )
