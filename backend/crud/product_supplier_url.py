# -*- coding: utf-8 -*-
"""
产品-供应商-URL CRUD
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.product_supplier_url import PrdProductSupplierUrl
from models.customer_product import PrdCustomerProduct
from models.supplier import SupSupplier
from schemas.product_supplier_url import ProductSupplierUrlCreate, ProductSupplierUrlUpdate
from fastapi import HTTPException


def list_urls(
    db: Session,
    product_id: int,
    supplier_id: int | None = None,
    supplier_name: str | None = None,
) -> list[PrdProductSupplierUrl]:
    """查询 URL 列表：优先 supplier_id；只有当 primary lookup 返回空 AND supplier_name 非空时，
    才回退到 (supplier_id IS NULL AND supplier_name == supplier_name) 匹配历史导入数据。"""
    q = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == product_id
    )

    if supplier_id is not None:
        # 主分支：按 supplier_id 精确匹配
        rows = q.filter(PrdProductSupplierUrl.supplier_id == supplier_id).all()
        if rows:
            return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))
        # fallback：仅当 supplier_name 提供时，匹配 supplier_id IS NULL 的历史数据
        if supplier_name:
            rows = q.filter(
                PrdProductSupplierUrl.supplier_id.is_(None),
                PrdProductSupplierUrl.supplier_name == supplier_name,
            ).all()
            return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))
        return []

    if supplier_name:
        # supplier_id 为 None 时：仅匹配历史 NULL 记录（避免返回所有 NULL 记录）
        rows = q.filter(
            PrdProductSupplierUrl.supplier_id.is_(None),
            PrdProductSupplierUrl.supplier_name == supplier_name,
        ).all()
        return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))

    # 两者都未提供：返回该 product 全部记录
    rows = q.all()
    return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))


def create_url(db: Session, data: ProductSupplierUrlCreate) -> tuple[PrdProductSupplierUrl, bool]:
    """创建 URL：supplier_id 已改为必需；处理重复 + is_default 升级 + 并发 IntegrityError"""
    if data.supplier_id is None:
        raise HTTPException(status_code=422, detail="supplier_id 不能为空")

    # 校验 product 与 supplier 存在性
    product = db.query(PrdCustomerProduct).filter(PrdCustomerProduct.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    supplier = db.query(SupSupplier).filter(SupSupplier.id == data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    # TODO: add dept ownership check

    existing = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == data.product_id,
        PrdProductSupplierUrl.supplier_id == data.supplier_id,
        PrdProductSupplierUrl.url == data.url,
    ).first()

    if existing:
        if data.is_default and not existing.is_default:
            _clear_other_defaults(db, data.product_id, data.supplier_id, exclude_id=existing.id)
            existing.is_default = True
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                return _refetch_existing(db, data), False
            db.refresh(existing)
        return existing, False

    if data.is_default:
        _clear_other_defaults(db, data.product_id, data.supplier_id)

    url = PrdProductSupplierUrl(**data.model_dump())
    try:
        db.add(url)
        db.commit()
    except IntegrityError:
        db.rollback()
        return _refetch_existing(db, data), False
    db.refresh(url)
    return url, True


def _refetch_existing(db: Session, data: ProductSupplierUrlCreate) -> PrdProductSupplierUrl | None:
    return db.query(PrdProductSupplierUrl).filter_by(
        product_id=data.product_id,
        supplier_id=data.supplier_id,
        url=data.url,
    ).first()


def get_url(db: Session, url_id: int) -> PrdProductSupplierUrl | None:
    """根据 ID 获取单条 URL 记录"""
    return db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.id == url_id).first()


def update_url(db: Session, url_id: int, data: ProductSupplierUrlUpdate) -> PrdProductSupplierUrl | None:
    url = get_url(db, url_id)
    if not url:
        return None

    # 历史只读数据（supplier_id IS NULL）禁止修改
    if url.supplier_id is None:
        raise HTTPException(status_code=409, detail="历史只读数据，禁止修改")

    # URL 冲突检查
    if data.url and data.url != url.url:
        conflict = db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == url.product_id,
            PrdProductSupplierUrl.supplier_id == url.supplier_id,
            PrdProductSupplierUrl.url == data.url,
            PrdProductSupplierUrl.id != url_id,
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="URL 已存在同产品同供应商下的另一条记录")

    if data.is_default is True and not url.is_default:
        _promote_to_default(db, url)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(url, field, value)

    db.commit()
    db.refresh(url)
    return url


def delete_url(db: Session, url_id: int) -> bool:
    url = get_url(db, url_id)
    if not url:
        return False

    # 历史只读数据（supplier_id IS NULL）禁止删除
    if url.supplier_id is None:
        raise HTTPException(status_code=409, detail="历史只读数据，禁止删除")

    was_default = url.is_default
    db.delete(url)
    db.commit()

    if was_default:
        # 删除默认 URL 后，自动选择最新一条为默认
        next_default = db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == url.product_id,
            PrdProductSupplierUrl.supplier_id == url.supplier_id,
            PrdProductSupplierUrl.id != url_id,
        ).order_by(PrdProductSupplierUrl.created_at.desc()).first()
        if next_default:
            next_default.is_default = True
            db.commit()

    return True


# ---- Helpers ----

def _promote_to_default(db: Session, url: PrdProductSupplierUrl):
    _clear_other_defaults(db, url.product_id, url.supplier_id, exclude_id=url.id)
    url.is_default = True


def _clear_other_defaults(
    db: Session,
    product_id: int,
    supplier_id: int | None,
    exclude_id: int | None = None,
):
    q = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == product_id,
        PrdProductSupplierUrl.supplier_id == supplier_id,
    )
    if exclude_id is not None:
        q = q.filter(PrdProductSupplierUrl.id != exclude_id)
    q.update({"is_default": False})
