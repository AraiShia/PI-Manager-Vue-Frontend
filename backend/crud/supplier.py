from sqlalchemy.orm import Session, joinedload
from typing import Optional
from models import SupSupplier, SupSupplierContact
from schemas import SupplierCreate, SupplierUpdate
from region_data import get_city_code


def split_region(region: str | None) -> tuple[str | None, str | None]:
    if not region:
        return None, None
    parts = [part.strip() for part in str(region).split() if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], None
    return None, None


def enrich_supplier(supplier: SupSupplier | None) -> SupSupplier | None:
    if not supplier:
        return None
    province, city = split_region(supplier.region)
    setattr(supplier, "province", province)
    setattr(supplier, "city", city)
    setattr(supplier, "city_code", get_city_code(province, city) if province and city else None)
    return supplier

def int_to_base32(n):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
    return chars[n]

def generate_supplier_code(db: Session, city_code: str) -> str:
    prefix = f"SP{city_code}" if city_code else "SP000"
    base_query = db.query(SupSupplier.supplier_code).filter(
        SupSupplier.supplier_code.like(f"{prefix}%")
    ).order_by(SupSupplier.supplier_code.desc())

    max_code = base_query.first()

    if max_code:
        suffix = max_code[0][len(prefix):]
        if len(suffix) == 3:
            try:
                last_num = int(suffix)
                next_num = last_num + 1
                return f"{prefix}{str(next_num).zfill(3)}"
            except ValueError:
                pass

    return f"{prefix}001"

def _validate_platform_fields(supplier: SupplierCreate) -> None:
    """按 platform 强校验关键字段（运行时）"""
    if supplier.platform == '1688':
        if not supplier.shop_link or not supplier.shop_link.strip():
            raise ValueError('1688 供应商必须填写店铺链接')
    elif supplier.platform == 'wechat':
        if not supplier.supplier_name or not supplier.supplier_name.strip():
            raise ValueError('微信供应商名称（微信号）不能为空')


def create_supplier(db: Session, supplier: SupplierCreate, dept_id: str = "S") -> SupSupplier:
    _validate_platform_fields(supplier)  # 平台强校验
    city_code = supplier.city_code or "000"
    supplier_code = generate_supplier_code(db, city_code)

    region = f"{supplier.province} {supplier.city}" if supplier.province and supplier.city else ""

    db_supplier = SupSupplier(
        supplier_code=supplier_code,
        dept_id=dept_id,
        supplier_name=supplier.supplier_name,
        region=region,
        platform=supplier.platform,
        shop_link=supplier.shop_link,
        wechat_id=supplier.wechat_id,
        wechat_nickname=supplier.wechat_nickname,
        is_dropship=bool(supplier.is_dropship) if supplier.is_dropship is not None else False,
    )

    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)

    if supplier.contact_person or supplier.phone or supplier.email or supplier.address:
        contact = SupSupplierContact(
            supplier_id=db_supplier.id,
            name=supplier.contact_person,
            phone=supplier.phone,
            email=supplier.email,
            address=supplier.address,
            is_primary=1
        )
        db.add(contact)
        db.commit()

    return enrich_supplier(db_supplier)

def get_supplier(db: Session, supplier_id: int) -> SupSupplier:
    return enrich_supplier(db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first())

def get_supplier_by_code(db: Session, supplier_code: str) -> SupSupplier:
    return db.query(SupSupplier).filter(SupSupplier.supplier_code == supplier_code).first()

def get_supplier_by_name(db: Session, supplier_name: str, dept_id: str = "S") -> SupSupplier:
    """按名称精确查找供应商（同部门内）"""
    if not supplier_name:
        return None
    return db.query(SupSupplier).filter(
        SupSupplier.supplier_name == supplier_name,
        SupSupplier.dept_id == dept_id,
    ).first()


def get_supplier_by_name_and_platform(
    db: Session,
    supplier_name: str,
    platform: Optional[str] = None,
    dept_id: str = "S",
) -> Optional[SupSupplier]:
    """按部门 + 平台 + 名称精确查找供应商（线上采购场景）

    Args:
        platform: 必填且非空；调用方需保证已通过 Literal / 业务校验
    """
    if not supplier_name:
        return None
    query = db.query(SupSupplier).filter(
        SupSupplier.supplier_name == supplier_name,
        SupSupplier.dept_id == dept_id,
    )
    if platform:
        query = query.filter(SupSupplier.platform == platform)
    return query.first()


def find_or_create_supplier_by_name(
    db: Session,
    supplier_name: str,
    platform: str,  # 必填，调用方须保证非空；放在所有带默认值参数之前
    dept_id: str = "S",
    contact_person: str = None,
    phone: str = None,
    address: str = None,
    shop_link: Optional[str] = None,
    wechat_id: Optional[str] = None,
    wechat_nickname: Optional[str] = None,
    is_dropship: Optional[bool] = None,
) -> tuple[SupSupplier, bool]:
    """2026-07-20：线上采购按 dept_id + platform + supplier_name 查找或创建供应商

    返回 (supplier, created)：
    - created=True  → 本次调用新创建了供应商
    - created=False → 命中已有供应商（可能已补齐缺失字段）

    前提：platform 必须非空（'1688'/'wechat'/'offline'），调用方应确保线上采购必传。

    流程：
    1. 运行时校验 platform ∈ ('1688','wechat','offline')，否则 ValueError
    2. 按 supplier_name + dept_id + platform 精确查找现有供应商
    3. 找到 → 补齐缺失字段后返回 (existing, False)
    4. 找不到 → 用 SupplierCreate 创建，返回 (new_supplier, True)
    """
    if not supplier_name or not supplier_name.strip():
        return None
    supplier_name = supplier_name.strip()

    # 运行时校验 platform：Python 类型标注不会阻止 None/空串
    if platform not in ('1688', 'wechat', 'offline'):
        raise ValueError('无效或缺失的供应商平台：必须是 1688 / wechat / offline')

    existing = get_supplier_by_name_and_platform(db, supplier_name, platform, dept_id)
    if existing:
        # 1688 命中后必须补齐 shop_link
        if platform == '1688' and not (existing.shop_link or shop_link):
            raise ValueError('1688 供应商必须填写店铺链接，可在供应商详情中补充后重试')
        # 补齐缺失字段（wechat_nickname/is_dropship 等）
        updated = False
        if platform == '1688' and not existing.shop_link and shop_link:
            existing.shop_link = shop_link
            updated = True
        if wechat_id and not existing.wechat_id:
            existing.wechat_id = wechat_id
            updated = True
        if wechat_nickname and not existing.wechat_nickname:
            existing.wechat_nickname = wechat_nickname
            updated = True
        if is_dropship is not None and existing.is_dropship is False:
            existing.is_dropship = bool(is_dropship)
            updated = True
        if updated:
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return (existing, False)  # created=False 表示复用已有

    # 创建新供应商（透传平台字段）
    create_payload = SupplierCreate(
        supplier_name=supplier_name,
        contact_person=contact_person or "",
        phone=phone or "",
        address=address or "",
        platform=platform,
        shop_link=shop_link,
        wechat_id=wechat_id,
        wechat_nickname=wechat_nickname,
        is_dropship=bool(is_dropship) if is_dropship is not None else False,
    )
    new_supplier = create_supplier(db, create_payload, dept_id)
    return (new_supplier, True)  # created=True 表示新建

def get_suppliers(db: Session, skip: int = 0, limit: int = 100, keyword: str | None = None):
    query = db.query(SupSupplier).options(
        joinedload(SupSupplier.contacts)
    )
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            (SupSupplier.supplier_name.ilike(pattern)) |
            (SupSupplier.supplier_code.ilike(pattern))
        )
    suppliers = query.offset(skip).limit(limit).all()

    result = []
    for s in suppliers:
        province, city = split_region(s.region)
        supplier_dict = {
            "id": s.id,
            "supplier_code": s.supplier_code,
            "supplier_name": s.supplier_name,
            "region": s.region,
            "province": province,
            "city": city,
            "dept_id": s.dept_id,
            "status": s.status,
            "created_at": s.created_at,
            "platform": s.platform,
            "shop_link": s.shop_link,
            "wechat_id": s.wechat_id,
            "wechat_nickname": s.wechat_nickname,
            "is_dropship": s.is_dropship,
        }
        primary_contact = next((c for c in s.contacts if c.is_primary == 1), None)
        if primary_contact:
            supplier_dict["contact_person"] = getattr(primary_contact, 'name', None)
            supplier_dict["phone"] = getattr(primary_contact, 'phone', None)
            supplier_dict["email"] = getattr(primary_contact, 'email', None)
            supplier_dict["address"] = getattr(primary_contact, 'address', None)
        result.append(supplier_dict)
    return result

def _validate_platform_fields_update(db_supplier: SupSupplier, supplier_update: SupplierUpdate) -> None:
    """更新时平台字段校验

    规则：
    1. platform 已存在时禁止修改（前端 UI 锁定，后端拒绝变更）
    2. platform=NULL 允许首次设置（历史数据分配平台）
    3. 用"数据库旧值 + 本次更新值"合并后的最终值校验必填字段
    """
    if db_supplier.platform is not None and supplier_update.platform is not None:
        if supplier_update.platform != db_supplier.platform:
            raise ValueError(f'供应商平台不可修改（当前为 {db_supplier.platform}）')

    final_platform = supplier_update.platform if supplier_update.platform is not None else db_supplier.platform
    final_shop_link = supplier_update.shop_link if supplier_update.shop_link is not None else db_supplier.shop_link

    if final_platform == '1688' and not (final_shop_link and str(final_shop_link).strip()):
        raise ValueError('1688 供应商必须填写店铺链接')


def update_supplier(db: Session, supplier_id: int, supplier_update: SupplierUpdate) -> SupSupplier:
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None

    _validate_platform_fields_update(db_supplier, supplier_update)  # 平台变更锁定

    update_data = supplier_update.dict(exclude_unset=True)
    province = update_data.pop("province", None)
    city = update_data.pop("city", None)
    update_data.pop("city_code", None)

    if province is not None or city is not None:
        db_supplier.region = f"{province or ''} {city or ''}".strip()

    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    db.commit()
    db.refresh(db_supplier)
    return enrich_supplier(db_supplier)

def delete_supplier(db: Session, supplier_id: int) -> bool:
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return False

    for contact in db_supplier.contacts:
        db.delete(contact)
    
    db.delete(db_supplier)
    db.commit()
    return True

def batch_create_suppliers(db: Session, supplier_list: list, dept_id: str = "S") -> dict:
    success_count = 0
    fail_count = 0
    failed_items = []
    
    for idx, supplier_data in enumerate(supplier_list):
        try:
            supplier_create = SupplierCreate(**supplier_data)
            result = create_supplier(db, supplier_create, dept_id)
            success_count += 1
        except Exception as e:
            fail_count += 1
            failed_items.append({
                "index": idx,
                "supplier_name": supplier_data.get("supplier_name", "未知"),
                "error": str(e)
            })
    
    return {
        "total": len(supplier_list),
        "success": success_count,
        "failed": fail_count,
        "failed_items": failed_items
    }
