# -*- coding: utf-8 -*-
"""
产品-供应商-URL Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ProductSupplierUrlCreate(BaseModel):
    product_id: int
    supplier_id: int
    supplier_name: str
    url: str = Field(..., max_length=500)
    display_name: Optional[str] = None
    is_default: bool = False

    @field_validator('url')
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v:
            return v
        v_stripped = v.strip()
        if not (v_stripped.startswith('http://') or v_stripped.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v_stripped


class ProductSupplierUrlUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=500)
    display_name: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator('url')
    @classmethod
    def url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_stripped = v.strip()
        if not (v_stripped.startswith('http://') or v_stripped.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v_stripped


class ProductSupplierUrlResponse(BaseModel):
    id: int
    product_id: int
    supplier_id: Optional[int]
    supplier_name: str
    url: str
    display_name: Optional[str]
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}
