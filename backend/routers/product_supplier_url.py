# -*- coding: utf-8 -*-
"""
产品-供应商-URL API 路由

事务边界统一：本路由层负责 commit；CRUD 层仅 flush 不 commit。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
    """创建 URL。201 = 新建；200 = 已存在（重复 POST 幂等返回）。"""
    try:
        url, created = crud.create_url(db, data)
    except HTTPException:
        # CRUD 层 4xx 直接透传
        raise
    try:
        db.commit()
    except IntegrityError:
        # flush 时未触发的并发约束，统一提交时再次兜底
        db.rollback()
        url = crud._refetch_existing(db, data)
        if not url:
            raise HTTPException(status_code=409, detail="URL 已存在或并发冲突")
        return JSONResponse(
            content=jsonable_encoder(ProductSupplierUrlResponse.model_validate(url)),
            status_code=200,
        )

    status_code = 201 if created else 200
    return JSONResponse(
        content=jsonable_encoder(ProductSupplierUrlResponse.model_validate(url)),
        status_code=status_code,
    )


@router.put("/{url_id}", response_model=ProductSupplierUrlResponse)
def update_url(url_id: int, data: ProductSupplierUrlUpdate, db: Session = Depends(get_db)):
    """更新 URL。"""
    try:
        url = crud.update_url(db, url_id, data)
    except HTTPException:
        raise
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="URL 已存在或并发冲突")
    db.refresh(url)
    return url


@router.delete("/{url_id}", status_code=204)
def delete_url(
    url_id: int,
    db: Session = Depends(get_db),
):
    """删除 URL。删除默认项时自动提升最新一条。"""
    url = crud.get_url(db, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    if url.supplier_id is None:
        # 历史只读数据，禁止删除
        raise HTTPException(status_code=409, detail="历史只读数据，禁止删除")
    # TODO: add dept ownership check

    crud.delete_url(db, url_id)
    db.commit()
    # 路由层返回 204，无 body
    return None