# -*- coding: utf-8 -*-
"""
产品-供应商-URL API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.database import get_db
from schemas.product_supplier_url import (
    ProductSupplierUrlCreate,
    ProductSupplierUrlUpdate,
    ProductSupplierUrlResponse,
)
from crud import product_supplier_url as crud


router = APIRouter(prefix="/product-supplier-urls", tags=["product-supplier-urls"])


@router.get("", response_model=list[ProductSupplierUrlResponse])
def list_urls(
    product_id: int = Query(...),
    supplier_id: int | None = Query(None),
    supplier_name: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """按 (product_id, supplier_id) 查询；缺 supplier_id 时按 supplier_name fallback"""
    return crud.list_urls(db, product_id, supplier_id, supplier_name)


@router.post("", response_model=ProductSupplierUrlResponse)
def create_url(data: ProductSupplierUrlCreate, db: Session = Depends(get_db)):
    url, created = crud.create_url(db, data)
    # 201 Created 表示新建，200 OK 表示已存在
    if created:
        return JSONResponse(
            content=jsonable_encoder(ProductSupplierUrlResponse.model_validate(url)),
            status_code=201,
        )
    return JSONResponse(
        content=jsonable_encoder(ProductSupplierUrlResponse.model_validate(url)),
        status_code=200,
    )


@router.put("/{url_id}", response_model=ProductSupplierUrlResponse)
def update_url(url_id: int, data: ProductSupplierUrlUpdate, db: Session = Depends(get_db)):
    try:
        url = crud.update_url(db, url_id, data)
    except HTTPException:
        raise
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


@router.delete("/{url_id}", status_code=204)
def delete_url(
    url_id: int,
    db: Session = Depends(get_db),
):
    from models.customer import CrmCustomer
    from models.customer_product import PrdCustomerProduct
    url = crud.get_url(db, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    if url.supplier_id is None:
        # 历史只读数据，禁止删除
        raise HTTPException(status_code=409, detail="历史只读数据，禁止删除")
    # TODO: add dept ownership check
    crud.delete_url(db, url_id)
