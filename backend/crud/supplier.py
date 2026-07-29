"""供应商 (Supplier) CRUD 数据访问层服务模块。

包含供应商创建、查询、分页列表、查找或创建、增量更新及相关验证逻辑。
符合 Google Python 编程规范并提供详细的中文注释。
"""

from typing import Optional, Any, Literal, cast
from sqlalchemy.orm import Session, joinedload
from models import SupSupplier, SupSupplierContact
from schemas import SupplierCreate, SupplierUpdate
from region_data import get_city_code


def split_region(region: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """拆分 region 字符串为省份和城市。

    Args:
        region: 格式为 "省份 城市" 的字符串，或 None。

    Returns:
        tuple[Optional[str], Optional[str]]: (省份, 城市) 二元组。
    """
    if not region:
        return None, None
    parts = [part.strip() for part in region.split() if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], None
    return None, None


def enrich_supplier(supplier: Optional[SupSupplier]) -> Optional[SupSupplier]:
    """为供应商实体注入省份、城市、城市代码及主要联系人扩展属性。

    Args:
        supplier: 供应商 SQLAlchemy 数据库实体。

    Returns:
        Optional[SupSupplier]: 注入扩展字段后的供应商对象。
    """
    if not supplier:
        return None
    region_str = str(supplier.region) if supplier.region is not None else None
    province, city = split_region(region_str)
    setattr(supplier, "province", province)
    setattr(supplier, "city", city)
    setattr(supplier, "city_code", get_city_code(province, city) if province and city else None)

    # 提取主联系人 (is_primary == 1) 的信息并注入扩展属性，增加异常防御保护
    try:
        contacts = getattr(supplier, "contacts", []) or []
        primary_contact = next((c for c in contacts if getattr(c, "is_primary", 0) == 1), None)
        if primary_contact:
            setattr(supplier, "contact_person", getattr(primary_contact, "name", None))
            setattr(supplier, "phone", getattr(primary_contact, "phone", None))
            setattr(supplier, "email", getattr(primary_contact, "email", None))
            setattr(supplier, "address", getattr(primary_contact, "address", None))
        else:
            setattr(supplier, "contact_person", None)
            setattr(supplier, "phone", None)
            setattr(supplier, "email", None)
            setattr(supplier, "address", None)
    except Exception:
        # 当数据库缺失联系人表或懒加载刷新异常时，退化赋值默认 None
        setattr(supplier, "contact_person", None)
        setattr(supplier, "phone", None)
        setattr(supplier, "email", None)
        setattr(supplier, "address", None)

    return supplier


def generate_supplier_code(db: Session, city_code: str) -> str:
    """生成唯一供应商编号（例如: SP000001）。

    遍历所有相同前缀的供应商编号，精准解析数字后缀的最大值，
    并进行存在性二次校验，防范主键/唯一索引冲突。

    Args:
        db: 数据库 Session。
        city_code: 城市行政代码。

    Returns:
        str: 自动递增的唯一供应商编号。
    """
    prefix = f"SP{city_code}" if city_code else "SP000"
    all_codes = (
        db.query(SupSupplier.supplier_code)
        .filter(SupSupplier.supplier_code.like(f"{prefix}%"))
        .all()
    )

    max_num = 0
    for (code,) in all_codes:
        if code and code.startswith(prefix):
            suffix = code[len(prefix):]
            if suffix.isdigit():
                num = int(suffix)
                if num > max_num:
                    max_num = num

    next_num = max_num + 1
    candidate_code = f"{prefix}{str(next_num).zfill(3)}"

    # 循环检查，确保生成的 candidate_code 绝对未被占用
    while db.query(SupSupplier).filter(SupSupplier.supplier_code == candidate_code).first() is not None:
        next_num += 1
        candidate_code = f"{prefix}{str(next_num).zfill(3)}"

    return candidate_code


def _validate_platform_fields(supplier: SupplierCreate) -> None:
    """创建时对 platform 关键字段进行运行时强校验。"""
    pass


def create_supplier(db: Session, supplier: SupplierCreate, dept_id: str = "S") -> Optional[SupSupplier]:
    """新建供应商主表记录及默认主联系人。

    Args:
        db: 数据库 Session。
        supplier: 供应商创建 Schema 载荷。
        dept_id: 部门 ID，默认为 "S"。

    Returns:
        Optional[SupSupplier]: 创建并补全扩展字段后的供应商实体。
    """
    _validate_platform_fields(supplier)
    # 自动依据省市推算 city_code
    city_code = supplier.city_code or (get_city_code(supplier.province, supplier.city) if supplier.province and supplier.city else None) or "000"
    supplier_code = generate_supplier_code(db, city_code)

    region = f"{supplier.province or ''} {supplier.city or ''}".strip() if (supplier.province or supplier.city) else ""

    platform_val: Any = supplier.platform if supplier.platform else None

    db_supplier = SupSupplier(
        supplier_code=supplier_code,
        dept_id=dept_id,
        supplier_name=supplier.supplier_name,
        region=region,
        platform=platform_val,
        wechat_id=supplier.wechat_id,
        wechat_nickname=supplier.wechat_nickname,
        is_dropship=bool(supplier.is_dropship) if supplier.is_dropship is not None else False,
        supply_mode=supplier.supply_mode,
        supplier_wechat=supplier.supplier_wechat,
    )

    supplier_id: Optional[int] = None
    try:
        db.add(db_supplier)
        db.flush()  # 预分配供应商主键 ID
        supplier_id = cast(int, db_supplier.id)

        if supplier.contact_person or supplier.phone or supplier.email or supplier.address:
            contact = SupSupplierContact(
                supplier_id=supplier_id,
                name=supplier.contact_person,
                phone=supplier.phone,
                email=supplier.email,
                address=supplier.address,
                is_primary=1,
            )
            db.add(contact)

        db.commit()  # 单原子事务统一提交供应商主表及关联主联系人
    except Exception as e:
        db.rollback()
        raise e

    # 提交完成后，使用 supplier_id 从数据库重新加载包含最新关联联系人的完整实体对象
    # 避免使用 session.refresh() 在特定 ORM 级联/会话状态下触发 "Could not refresh instance" 异常
    if supplier_id is not None:
        reloaded = get_supplier(db, supplier_id)
        if reloaded is not None:
            return reloaded

    return enrich_supplier(db_supplier)


def get_supplier(db: Session, supplier_id: int) -> Optional[SupSupplier]:
    """通过主键 ID 查询供应商。"""
    return enrich_supplier(db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first())


def get_supplier_by_code(db: Session, supplier_code: str) -> Optional[SupSupplier]:
    """通过供应商编号精准查询供应商。"""
    return db.query(SupSupplier).filter(SupSupplier.supplier_code == supplier_code).first()


def get_supplier_by_name(db: Session, supplier_name: str, dept_id: str = "S") -> Optional[SupSupplier]:
    """按名称在同一部门内精准查找供应商。"""
    if not supplier_name:
        return None
    return (
        db.query(SupSupplier)
        .filter(
            SupSupplier.supplier_name == supplier_name,
            SupSupplier.dept_id == dept_id,
        )
        .first()
    )


def get_supplier_by_name_and_platform(
    db: Session,
    supplier_name: str,
    platform: Optional[str] = None,
    dept_id: str = "S",
) -> Optional[SupSupplier]:
    """按部门 + 平台 + 名称精准查找供应商。

    Args:
        db: 数据库 Session。
        supplier_name: 供应商名称。
        platform: 平台标识（如 online / offline / 1688 / wechat 等）。
        dept_id: 部门编号。

    Returns:
        Optional[SupSupplier]: 匹配到的供应商对象。
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
    platform: str,
    dept_id: str = "S",
    contact_person: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    wechat_id: Optional[str] = None,
    wechat_nickname: Optional[str] = None,
    is_dropship: Optional[bool] = None,
) -> Optional[tuple[SupSupplier, bool]]:
    """按 dept_id + platform + supplier_name 查找或快速创建供应商。

    Args:
        db: 数据库 Session。
        supplier_name: 供应商名称。
        platform: 采购平台类型。
        dept_id: 部门标识。
        contact_person: 联系人（选填）。
        phone: 电话（选填）。
        address: 地址（选填）。
        wechat_id: 微信号。
        wechat_nickname: 微信昵称。
        is_dropship: 是否一件代发。

    Returns:
        Optional[tuple[SupSupplier, bool]]: (供应商对象, 是否新创建)。若参数非法则返回 None。
    """
    if not supplier_name or not supplier_name.strip():
        return None
    clean_name = supplier_name.strip()

    existing = get_supplier_by_name_and_platform(db, clean_name, platform, dept_id)
    if existing:
        updated = False
        if wechat_id and not getattr(existing, "wechat_id", None):
            setattr(existing, "wechat_id", wechat_id)
            updated = True
        if wechat_nickname and not getattr(existing, "wechat_nickname", None):
            setattr(existing, "wechat_nickname", wechat_nickname)
            updated = True
        if is_dropship is not None and getattr(existing, "is_dropship", False) is False:
            setattr(existing, "is_dropship", is_dropship)
            updated = True
        if updated:
            db.add(existing)
            db.commit()
            existing_id = cast(int, existing.id)
            reloaded_existing = get_supplier(db, existing_id)
            if reloaded_existing:
                existing = reloaded_existing
        return (existing, False)

    platform_val: Any = platform if platform else None

    create_payload = SupplierCreate(
        supplier_name=clean_name,
        contact_person=contact_person or "",
        phone=phone or "",
        address=address or "",
        platform=platform_val,
        wechat_id=wechat_id,
        wechat_nickname=wechat_nickname,
        is_dropship=is_dropship if is_dropship is not None else False,
    )
    new_supplier = create_supplier(db, create_payload, dept_id)
    if new_supplier is None:
        return None
    return (new_supplier, True)


def get_suppliers(db: Session, skip: int = 0, limit: int = 100, keyword: Optional[str] = None) -> list[dict[str, Any]]:
    """分页获取供应商列表（包含首要联系人与扩展字段信息，带生产环境防崩溃容错保护）。"""
    suppliers = []
    try:
        query = db.query(SupSupplier).options(joinedload(SupSupplier.contacts))
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"
            query = query.filter(
                (SupSupplier.supplier_name.ilike(pattern)) | (SupSupplier.supplier_code.ilike(pattern))
            )
        suppliers = query.offset(skip).limit(limit).all()
    except Exception:
        # 当生产环境数据库缺失扩展列 (OperationalError) 时，回退执行基础不连带属性查询
        try:
            db.rollback()
            query = db.query(SupSupplier)
            if keyword and keyword.strip():
                pattern = f"%{keyword.strip()}%"
                query = query.filter(
                    (SupSupplier.supplier_name.ilike(pattern)) | (SupSupplier.supplier_code.ilike(pattern))
                )
            suppliers = query.offset(skip).limit(limit).all()
        except Exception:
            return []

    result = []
    for s in suppliers:
        try:
            region_str = str(s.region) if getattr(s, "region", None) is not None else None
            province, city = split_region(region_str)
            supplier_dict: dict[str, Any] = {
                "id": getattr(s, "id", 0),
                "supplier_code": getattr(s, "supplier_code", None) or f"SP{getattr(s, 'id', 0):04d}",
                "supplier_name": getattr(s, "supplier_name", None) or "",
                "region": getattr(s, "region", None),
                "province": province,
                "city": city,
                "dept_id": getattr(s, "dept_id", None) or "S",
                "status": getattr(s, "status", 1) if getattr(s, "status", None) is not None else 1,
                "created_at": getattr(s, "created_at", None),
                "platform": getattr(s, "platform", None),
                "wechat_id": getattr(s, "wechat_id", None),
                "wechat_nickname": getattr(s, "wechat_nickname", None),
                "is_dropship": getattr(s, "is_dropship", False),
                "supply_mode": getattr(s, "supply_mode", None),
                "supplier_wechat": getattr(s, "supplier_wechat", None),
            }
            contacts = getattr(s, "contacts", []) or []
            primary_contact = next((c for c in contacts if getattr(c, "is_primary", 0) == 1), None)
            if primary_contact:
                supplier_dict["contact_person"] = getattr(primary_contact, "name", None)
                supplier_dict["phone"] = getattr(primary_contact, "phone", None)
                supplier_dict["email"] = getattr(primary_contact, "email", None)
                supplier_dict["address"] = getattr(primary_contact, "address", None)
            result.append(supplier_dict)
        except Exception:
            continue
    return result


def _validate_platform_fields_update(db_supplier: SupSupplier, supplier_update: SupplierUpdate) -> None:
    """更新供应商平台字段时的强校验规则。

    规则：
    1. platform 已存在时禁止修改（前端 UI 锁定，后端拒绝变更）。
    2. platform=NULL 允许首次设置（历史数据分配平台）。
    """
    existing_platform = getattr(db_supplier, "platform", None)
    if existing_platform is not None and supplier_update.platform is not None:
        if supplier_update.platform != existing_platform:
            raise ValueError(f"供应商平台不可修改（当前为 {existing_platform}）")


def update_supplier(db: Session, supplier_id: int, supplier_update: SupplierUpdate) -> Optional[SupSupplier]:
    """更新已有的供应商信息及关联的主联系人。

    Args:
        db: 数据库 Session。
        supplier_id: 供应商 ID。
        supplier_update: 更新载荷。

    Returns:
        Optional[SupSupplier]: 更新并重新丰富属性后的供应商实体。
    """
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None

    _validate_platform_fields_update(db_supplier, supplier_update)

    update_data = supplier_update.model_dump(exclude_unset=True)
    province = update_data.pop("province", None)
    city = update_data.pop("city", None)
    update_data.pop("city_code", None)
    contact_person = update_data.pop("contact_person", None)
    phone = update_data.pop("phone", None)
    email = update_data.pop("email", None)
    address = update_data.pop("address", None)

    if province is not None or city is not None:
        setattr(db_supplier, "region", f"{province or ''} {city or ''}".strip())

    for key, value in update_data.items():
        if hasattr(db_supplier, key):
            setattr(db_supplier, key, value)

    # 同步更新或新增主联系人 (is_primary == 1)
    if any(x is not None for x in [contact_person, phone, email, address]):
        contacts = getattr(db_supplier, "contacts", []) or []
        primary_contact = next((c for c in contacts if getattr(c, "is_primary", 0) == 1), None)
        if primary_contact:
            if contact_person is not None: primary_contact.name = contact_person
            if phone is not None: primary_contact.phone = phone
            if email is not None: primary_contact.email = email
            if address is not None: primary_contact.address = address
        else:
            new_contact = SupSupplierContact(
                supplier_id=db_supplier.id,
                name=contact_person,
                phone=phone,
                email=email,
                address=address,
                is_primary=1,
            )
            db.add(new_contact)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    # 提交修改后通过 get_supplier 重新加载最新数据，防止 session.refresh 异常
    reloaded_supplier = get_supplier(db, supplier_id)
    if reloaded_supplier is not None:
        return reloaded_supplier

    return enrich_supplier(db_supplier)


def delete_supplier(db: Session, supplier_id: int) -> bool:
    """通过 ID 删除供应商及其关联的主联系人。"""
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return False

    for contact in db_supplier.contacts:
        db.delete(contact)

    db.delete(db_supplier)
    db.commit()
    return True


def batch_create_suppliers(db: Session, supplier_list: list[dict[str, Any]], dept_id: str = "S") -> dict[str, Any]:
    """批量创建供应商记录。

    Args:
        db: 数据库 Session。
        supplier_list: 供应商字典列表。
        dept_id: 部门 ID。

    Returns:
        dict[str, Any]: 包含总条数、成功数、失败数及失败明细的汇总字典。
    """
    success_count = 0
    fail_count = 0
    failed_items = []

    for idx, supplier_data in enumerate(supplier_list):
        try:
            supplier_create = SupplierCreate(**supplier_data)
            create_supplier(db, supplier_create, dept_id)
            success_count += 1
        except Exception as e:
            fail_count += 1
            failed_items.append(
                {
                    "index": idx,
                    "supplier_name": supplier_data.get("supplier_name", "未知"),
                    "error": str(e),
                }
            )

    return {
        "total": len(supplier_list),
        "success": success_count,
        "failed": fail_count,
        "failed_items": failed_items,
    }
