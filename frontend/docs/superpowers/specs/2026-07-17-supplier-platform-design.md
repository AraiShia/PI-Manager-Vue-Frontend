# 供应商平台分类改造设计

## 背景与目标

当前 `SupplierFormDialog` 为通用供应商表单，缺少线上采购（1688/微信）场景的关键字段，所有字段一股脑展示导致表单冗余。

本次改造目标：
1. 按采购平台（1688 / 微信 / 线下）分类管理供应商
2. 各平台供应商包含差异化字段
3. 前端表单动态适应平台类型
4. 线上采购自动建立 `supplier_id` 关联
5. 后端按平台强校验关键字段

## 数据模型

### 数据库层 — `sup_supplier` 表新增字段

| 字段 | 类型 | 默认值 | 可空 | 说明 |
|------|------|--------|------|------|
| `platform` | `VARCHAR(20)` | `NULL` | 是 | `'1688'` / `'wechat'` / `'offline'` / `NULL`（历史数据） |
| `shop_link` | `VARCHAR(500)` | `NULL` | 是 | 1688 店铺链接 |
| `wechat_id` | `VARCHAR(100)` | `NULL` | 是 | 1688 微信号 / 微信微信号 |
| `wechat_nickname` | `VARCHAR(100)` | `NULL` | 是 | 微信昵称 |
| `is_dropship` | `BOOLEAN` | `0` | 否（default） | 微信是否支持代发 |

**`wangwang` 字段说明**：原方案中包含 `wangwang`（旺旺 ID），后删除。生产环境如已有数据，**保留现有字段**（不删除列），但前端不再使用；如有迁移需求，下一期评估。

### 前端类型 — `@/api/suppliers`

```typescript
export interface Supplier {
  // ... 现有字段 ...
  platform?: '1688' | 'wechat' | 'offline' | null
  shop_link?: string | null       // 1688 店铺链接（1688 必填）
  wechat_id?: string | null       // 1688 选填 / 微信即 supplier_name
  wechat_nickname?: string | null // 微信昵称（微信选填）
  is_dropship?: boolean | null    // 是否支持代发（微信选填）
}

export interface SupplierFormPayload {
  // ... 现有字段 ...
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}
```

## 历史数据策略

历史供应商（`platform IS NULL`）的编辑行为：

- **编辑时显示全部三个 Tabs**（1688 / 微信 / 线下）
- 用户切换 Tabs 时弹窗确认（"切换平台会修改字段必填规则，是否继续？"）
- 提交保存时回写 `platform`，不再为 NULL
- 查询列表时无需处理 NULL（前端按 platform 显示标识，NULL 归为"未分类"标签）

## 后端 — Pydantic Schema 完整定义

`SupplierBase` 中 `dept_id` 和 `supplier_code` 为必填，但**仅用于响应**（`SupplierResponse` 继承自 `SupplierBase`）；`SupplierCreate` 不继承 `SupplierBase`，**不要求 `supplier_code`**，由后端 `generate_supplier_code()` 自动生成。

### `backend/schemas/supplier.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class SupplierBase(BaseModel):
    dept_id: str
    supplier_code: str
    supplier_name: str
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
    # 平台分类字段
    platform: Optional[Literal['1688', 'wechat', 'offline']] = None
    shop_link: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = False

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
    # 平台分类字段
    platform: Optional[Literal['1688', 'wechat', 'offline']] = None
    shop_link: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None

class SupplierResponse(SupplierBase):
    id: int
    status: int = 1
    created_at: datetime
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    # 平台分类字段（用于前端读取并回填表单）
    platform: Optional[str] = None
    shop_link: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None

    class Config:
        from_attributes = True
```

**前后端编号规则**：

- 后端 `crud.create_supplier` 中调用 `generate_supplier_code(db, city_code)` 自动生成
- 前端 `SupplierFormPayload` 不包含 `supplier_code` 字段
- 前端表单对应"供应商编号"字段**禁用输入**（`el-input :disabled="true"`），仅作为展示
- 表格列展示后端返回的 `supplier_code` 即可

## 后端 — CRUD 完整实现

### `backend/models/supplier.py` — SupSupplier 新增字段

```python
from sqlalchemy import Column, String, Integer, Boolean, ...

class SupSupplier(Base):
    __tablename__ = "sup_supplier"

    # ... 现有字段 ...
    platform = Column(String(20), nullable=True)
    shop_link = Column(String(500), nullable=True)
    wechat_id = Column(String(100), nullable=True)
    wechat_nickname = Column(String(100), nullable=True)
    is_dropship = Column(Boolean, default=False, nullable=False, server_default='0')
```

### `backend/crud/supplier.py` — 平台校验与字段透传

```python
# 在 create_supplier 顶部增加平台校验
def _validate_platform_fields(supplier: SupplierCreate):
    """按 platform 强校验关键字段"""
    if supplier.platform == '1688':
        if not supplier.shop_link or not supplier.shop_link.strip():
            raise ValueError('1688 供应商必须填写店铺链接')
    elif supplier.platform == 'wechat':
        if not supplier.supplier_name or not supplier.supplier_name.strip():
            raise ValueError('微信供应商名称（微信号）不能为空')

def create_supplier(db: Session, supplier: SupplierCreate, dept_id: str = "S") -> SupSupplier:
    _validate_platform_fields(supplier)  # 新增校验
    # ... 现有逻辑 ...
    db_supplier = SupSupplier(
        # ... 现有字段 ...
        platform=supplier.platform,
        shop_link=supplier.shop_link,
        wechat_id=supplier.wechat_id,
        wechat_nickname=supplier.wechat_nickname,
        is_dropship=supplier.is_dropship or False,
    )
    # ... commit / refresh / enrich ...

def _validate_platform_fields_update(db_supplier: SupSupplier, supplier_update: SupplierUpdate):
    """更新时平台字段校验

    校验规则：
    1. platform 为 NULL 时允许首次设置（历史数据首次分配平台）
    2. platform 已存在时禁止修改（前端 UI 锁定，后端拒绝变更）
    3. 使用"数据库旧值 + 本次更新值"合并后的最终值校验必填字段
    """
    # 历史 NULL 允许首次设置平台
    if db_supplier.platform is not None and supplier_update.platform is not None:
        if supplier_update.platform != db_supplier.platform:
            raise ValueError(f'供应商平台不可修改（当前为 {db_supplier.platform}）')

    final_platform = supplier_update.platform if supplier_update.platform is not None else db_supplier.platform
    final_shop_link = supplier_update.shop_link if supplier_update.shop_link is not None else db_supplier.shop_link

    if final_platform == '1688' and not (final_shop_link and final_shop_link.strip()):
        raise ValueError('1688 供应商必须填写店铺链接')


def update_supplier(db: Session, supplier_id: int, supplier_update: SupplierUpdate) -> SupSupplier:
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None
    _validate_platform_fields_update(db_supplier, supplier_update)  # 新增校验
    # ... 现有 update 逻辑（for key, value in update_data.items(): setattr(db_supplier, key, value)）...
```

### `backend/crud/supplier.py` — get_suppliers 返回新字段

在 result 字典中追加：

```python
supplier_dict["platform"] = s.platform
supplier_dict["shop_link"] = s.shop_link
supplier_dict["wechat_id"] = s.wechat_id
supplier_dict["wechat_nickname"] = s.wechat_nickname
supplier_dict["is_dropship"] = s.is_dropship
```

### `backend/crud/supplier.py` — 线上采购自动 find-or-create

新增 `platform`、`shop_link` 等平台字段参数；查询时按 `dept_id + platform + supplier_name` 精确匹配：

```python
def get_supplier_by_name_and_platform(
    db: Session,
    supplier_name: str,
    platform: Optional[str] = None,
    dept_id: str = "S",
) -> Optional[SupSupplier]:
    """按部门 + 平台 + 名称精确查找供应商"""
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
    """线上采购按 dept_id + platform + supplier_name 查找或创建供应商

    返回 (supplier, created)：
    - created=True  → 本次调用新创建了供应商
    - created=False → 命中已有供应商（可能已补齐缺失字段）

    前提：platform 必须非空，调用方应确保线上采购必传 platform。

    数据库层并发安全：
    - 唯一索引：CREATE UNIQUE INDEX uq_supplier_dept_platform_name
      ON sup_supplier(dept_id, platform, supplier_name)
      （platform 为 NULL 时不参与唯一约束，历史 NULL 数据不受影响）
    - 创建时捕获 IntegrityError，并发冲突时回滚后重新查询并复用
    """
    if not supplier_name or not supplier_name.strip():
        return None
    supplier_name = supplier_name.strip()

    # 运行时校验 platform：Python 类型标注不会阻止 None/空串，必须强制三元校验
    if platform not in ('1688', 'wechat', 'offline'):
        raise ValueError('无效或缺失的供应商平台：必须是 1688 / wechat / offline')

    if platform:
        existing = get_supplier_by_name_and_platform(db, supplier_name, platform, dept_id)
        if existing:
            # 检查 1688 必填字段
            if platform == '1688' and not (existing.shop_link or shop_link):
                raise ValueError('1688 供应商必须填写店铺链接，可在供应商详情中补充后重试')
            # 补齐缺失字段并返回（created=False 表示复用）
            return _fill_and_return(db, existing, False,
                shop_link=shop_link, wechat_id=wechat_id,
                wechat_nickname=wechat_nickname, is_dropship=is_dropship)

    # 未找到，尝试创建（并发场景下可能触发唯一约束冲突）
    try:
        return _do_create_supplier(db, supplier_name, dept_id, platform,
            contact_person, phone, address, shop_link, wechat_id, wechat_nickname, is_dropship)
    except Exception as exc:
        # 并发冲突：唯一约束违反，重新查询并复用（created=False）
        if 'UNIQUE constraint' in str(exc) or 'duplicate' in str(exc).lower():
            db.rollback()
            existing = get_supplier_by_name_and_platform(db, supplier_name, platform, dept_id)
            if existing:
                if platform == '1688' and not existing.shop_link and not shop_link:
                    raise ValueError('1688 供应商缺少店铺链接，可在供应商详情中补充后重试')
                return _fill_and_return(db, existing, False,
                    shop_link=shop_link, wechat_id=wechat_id,
                    wechat_nickname=wechat_nickname, is_dropship=is_dropship)
        raise


def _do_create_supplier(...全部参数...) -> tuple[SupSupplier, bool]:
    """实际创建供应商，内部不处理冲突；返回 (supplier, True)"""
    _validate_platform_fields_create(...)  # 复用已有校验逻辑
    create_payload = SupplierCreate(...)
    supplier = create_supplier(db, create_payload, dept_id)
    return (supplier, True)


def _fill_and_return(db, existing, created: bool, **kwargs) -> tuple[SupSupplier, bool]:
    """补齐缺失字段并返回；created 参数决定返回的 created 值"""
    updated = False
    for field, value in kwargs.items():
        if value and getattr(existing, field) is None:
            setattr(existing, field, value)
            updated = True
    if updated:
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return (existing, created)
```

### `backend/routers/supplier.py` — find-or-create 接受 platform

```python
class FindOrCreateSupplierRequest(BaseModel):
    supplier_name: str
    dept_id: Optional[str] = "S"
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    platform: Literal['1688', 'wechat', 'offline']   # 必填，缺失返回 422
    shop_link: Optional[str] = None      # 新增：1688 店铺链接
    wechat_id: Optional[str] = None      # 新增：微信号
    wechat_nickname: Optional[str] = None # 新增：微信昵称
    is_dropship: Optional[bool] = None   # 新增：是否代发

@router.post("/find-or-create", response_model=FindOrCreateSupplierResponse)
def find_or_create_supplier_api(
    payload: FindOrCreateSupplierRequest,
    db: Session = Depends(get_db)
):
    # 空白名称拦截（None.strip() 会抛 AttributeError，必须先判 None）
    if not payload.supplier_name or not payload.supplier_name.strip():
        raise HTTPException(status_code=422, detail="supplier_name 不能为空")

    try:
        result = find_or_create_supplier_by_name(
            db,
            supplier_name=payload.supplier_name,
            platform=payload.platform,  # Literal 必填，路由层无需二次校验
            dept_id=payload.dept_id or "S",
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

    if not result:
        raise HTTPException(status_code=500, detail="创建供应商失败")

    new_supplier, created = result
    return FindOrCreateSupplierResponse(
        id=new_supplier.id,
        supplier_name=new_supplier.supplier_name,
        supplier_code=new_supplier.supplier_code,
        created=created,
    )
```

### `backend/routers/purchase.py`（或对应的采购路由）— 线上采购自动 find-or-create

线上采购的 `createOnlinePurchase` 入口：

```python
from fastapi import HTTPException

# 1. 两者都缺失或名称为纯空白时直接拒绝
# 注意：'   '.strip() == ''，所以必须用 strip 后再判 bool，避免纯空白绕过
has_supplier_name = bool(payload.supplier_name and payload.supplier_name.strip())
if not payload.supplier_id and not has_supplier_name:
    raise HTTPException(
        status_code=422,
        detail='supplier_id 或 supplier_name（非空）至少填写一个'
    )

# 2. 传入 supplier_id 时，校验供应商、部门、平台一致性
if payload.supplier_id:
    supplier = db.query(SupSupplier).filter(SupSupplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=422, detail='供应商不存在')
    # 2.1 部门一致性校验：防止跨部门误关联
    if supplier.dept_id != payload.dept_id:
        raise HTTPException(
            status_code=422,
            detail=f'所选供应商部门为 {supplier.dept_id}，与本次采购部门 {payload.dept_id} 不一致，'
                   '请选择本部门供应商或通过"新建供应商"创建'
        )
    # 2.2 平台校验：platform IS NULL 视为"未知平台"，线上采购禁止直接关联
    # 历史供应商必须先在"供应商管理"中补录平台，才能用于线上采购
    if supplier.platform is None:
        raise HTTPException(
            status_code=422,
            detail=f'所选供应商（{supplier.supplier_name}）尚未分配平台，无法关联到线上采购。'
                   '请先在"供应商管理"中为该供应商设置平台类型。'
        )
    # 2.3 平台一致性校验：防止跨平台误复用
    if supplier.platform != payload.platform:
        raise HTTPException(
            status_code=422,
            detail=f'所选供应商平台为 {supplier.platform}，与本次采购平台 {payload.platform} 不一致，'
                   '请重新选择或使用"新建供应商"流程'
        )
    # 一致则直接使用 supplier_id，无需 find-or-create

# 3. 未传 supplier_id 但有 supplier_name，按平台创建/查找
elif payload.supplier_name:
    # 透传 shop_link（1688 必填）、wechat_nickname 等平台字段
    supplier = find_or_create_supplier_by_name(
        db,
        supplier_name=payload.supplier_name,
        platform=payload.platform,  # 必填Literal，不会为空；platform 在 dept_id 之前
        dept_id=payload.dept_id,
        shop_link=getattr(payload, 'shop_link', None),  # 1688 必填
        wechat_id=getattr(payload, 'wechat_id', None),  # 1688 选填
        wechat_nickname=getattr(payload, 'wechat_nickname', None),  # 微信选填
        is_dropship=getattr(payload, 'is_dropship', None),
        contact_person=getattr(payload, 'supplier_contact', None),
        phone=getattr(payload, 'supplier_phone', None),
    )
    if supplier:
        payload.supplier_id = supplier.id  # 写入采购单
```

采购单 platform 字段以请求 `payload.platform` 为准（采购单本身记录本次采购的平台类型），与供应商 platform 一致性由后端校验。

### 采购请求契约完整定义

`backend/schemas/purchase.py`（或对应文件）需要明确以下字段：

```python
class PurchaseCreateOnline(BaseModel):
    # 现有字段保持不变
    dept_id: str
    pi_id: int
    supplier_id: Optional[int] = None      # 已有供应商时传入；后端校验平台一致性
    supplier_name: Optional[str] = None    # 1688 店铺名 / 微信昵称
    platform: Literal['1688', 'wechat']    # 必填，缺失返回 422
    items: List[PurchaseItem]
    link: Optional[str] = None
    contact_wechat: Optional[str] = None
    screenshot: Optional[str] = None
    remark: Optional[str] = None
    # 新增平台字段（与 supplier 表字段对齐）
    shop_link: Optional[str] = None        # 1688 店铺链接
    wechat_id: Optional[str] = None        # 微信号（1688 选填 / 微信即 supplier_name）
    wechat_nickname: Optional[str] = None  # 微信昵称
    is_dropship: Optional[bool] = None     # 是否支持代发
    # 线下联系人字段
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
```

`backend/models/purchase.py`（或对应 ORM）补齐字段：

```python
class PurchaseOrder(Base):
    # 现有字段...
    # 新增平台字段
    platform = Column(String(20), nullable=True)
    shop_link = Column(String(500), nullable=True)
    wechat_id = Column(String(100), nullable=True)
    wechat_nickname = Column(String(100), nullable=True)
    is_dropship = Column(Boolean, default=False, nullable=False, server_default='0')
```

采购路由 `create_online_purchase` 入参使用 `PurchaseCreateOnline`，落库前确保字段已包含（避免 Pydantic `extra='ignore'` 默认行为丢失）。

## 后端 — 数据库迁移（手写脚本，参考 `migrations/add_pi_item_labeling_fee.py` 风格）

### `backend/migrations/add_supplier_platform_fields.py`

```python
"""为供应商增加平台分类相关字段。"""

from sqlalchemy import text

from app.database import engine


def upgrade():
    with engine.connect() as conn:
        # 添加可空字段（不强制非空以兼容已有数据）
        for ddl in [
            "ALTER TABLE sup_supplier ADD COLUMN platform VARCHAR(20)",
            "ALTER TABLE sup_supplier ADD COLUMN shop_link VARCHAR(500)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_id VARCHAR(100)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_nickname VARCHAR(100)",
            # is_dropship 加 server_default='0' 让已有数据自动为 False
            "ALTER TABLE sup_supplier ADD COLUMN is_dropship BOOLEAN NOT NULL DEFAULT 0",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        # 创建唯一索引防止并发重复（仅在 (dept_id, platform, supplier_name) 全非 NULL 时生效）
        # platform 为 NULL 时不参与唯一约束，允许历史 NULL 数据保留

        # Step 1：检查已有重复数据（非 NULL platform）
        duplicate_rows = conn.execute(text("""
            SELECT dept_id, platform, supplier_name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
            FROM sup_supplier
            WHERE dept_id IS NOT NULL
              AND platform IS NOT NULL
              AND supplier_name IS NOT NULL
            GROUP BY dept_id, platform, supplier_name
            HAVING COUNT(*) > 1
        """)).fetchall()

        if duplicate_rows:
            # 发现重复，打印并中止迁移，要求人工处理
            for row in duplicate_rows:
                print(f"[MIGRATION ERROR] 重复供应商数据: dept_id={row[0]}, platform={row[1]}, "
                      f"supplier_name={row[2]}, 重复数量={row[3]}, ids={row[4]}")
            raise RuntimeError(
                f"发现 {len(duplicate_rows)} 组重复供应商数据，请先在数据库中合并或删除重复记录后再执行迁移。"
                "受影响组合：" + ", ".join(
                    f"({r[0]},{r[1]},{r[2]})" for r in duplicate_rows
                )
            )

        # Step 2：无重复，正式创建唯一索引
        try:
            conn.execute(text("""
                CREATE UNIQUE INDEX uq_supplier_dept_platform_name
                ON sup_supplier(dept_id, platform, supplier_name)
            """))
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                raise

        conn.commit()


if __name__ == "__main__":
    upgrade()
```

**Docker 容器内执行方式**：

镜像 `WORKDIR=/app`，且 `COPY . .` 将 backend 根目录复制为容器内的 `/app`，**不是** `/app/backend`：

```bash
# 在宿主机执行（推荐）
docker compose exec backend python -m migrations.add_supplier_platform_fields

# 或直接指定容器名（项目实际 container_name: pi-backend）
docker exec -it pi-backend python -m migrations.add_supplier_platform_fields
```

进入容器验证路径：

```bash
docker compose exec backend ls /app/migrations/add_supplier_platform_fields.py
# 应输出文件路径表示迁移脚本存在
docker compose exec backend pwd
# 应输出 /app（不是 /app/backend）
```

若需手动排查：

```bash
docker compose exec backend python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); cols = [row[1] for row in conn.execute(text('PRAGMA table_info(sup_supplier)')).fetchall()]; print('platform' in cols, 'shop_link' in cols, 'wechat_id' in cols, 'wechat_nickname' in cols, 'is_dropship' in cols)"
# 预期：True True True True True
```

## 前端 — SupplierFormDialog 完整改造

### Props

```typescript
const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
  /** 默认平台（新建时 Tabs 初始选中），默认 'offline' */
  defaultPlatform?: '1688' | 'wechat' | 'offline'
}>()
```

### Tabs 行为

```typescript
const currentPlatform = ref<'1688' | 'wechat' | 'offline'>(
  props.supplier?.platform || props.defaultPlatform || 'offline'
)
// 是否有 platform 历史（NULL 表示历史数据，可切换）
const hasPlatform = computed(() => !!props.supplier?.platform)
```

模板中：

```vue
<!-- 新建或历史数据（platform NULL）时 Tabs 可切换 -->
<el-tabs v-if="!props.supplier || !props.supplier.platform" v-model="currentPlatform">
  <el-tab-pane label="1688" name="1688" />
  <el-tab-pane label="微信" name="wechat" />
  <el-tab-pane label="线下" name="offline" />
</el-tabs>

<!-- 已有 platform 的供应商，Tabs 锁定为该值 -->
<div v-else class="platform-locked">
  <el-tag>{{ platformLabelMap[currentPlatform] }}</el-tag>
</div>
```

### 字段配置

**1688 供应商**：

| 字段 | 必填（前端） | 必填（后端） |
|------|------------|------------|
| 供应商编号 | 否 | 否 |
| 供应商名称 | 是 | 是 |
| 店铺链接 | 是 | **是** |
| 联系人 | 否 | 否 |
| 微信号 | 否 | 否 |
| 电话 | 否 | 否 |
| 省份/城市 | 否 | 否 |

**微信供应商**：

| 字段 | 必填（前端） | 必填（后端） |
|------|------------|------------|
| 供应商编号 | 否 | 否 |
| 供应商名称（微信号） | 是 | **是** |
| 微信昵称 | 否 | 否 |
| 是否支持代发 | 否 | 否 |
| 联系人 | 否 | 否 |
| 电话 | 否 | 否 |
| 省份/城市 | 否 | 否 |

**线下供应商**：保持现状全部字段可选。

### 前端表单校验

```typescript
const rules: FormRules = {
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  shop_link: [{
    validator: (rule, value, callback) => {
      if (currentPlatform.value === '1688' && !value?.trim()) {
        callback(new Error('1688 供应商必须填写店铺链接'))
      } else {
        callback()
      }
    },
    trigger: 'blur',
  }],
}
```

### 保存逻辑

```typescript
async function save() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: SupplierFormPayload = {
      supplier_name: form.supplier_name,
      province: form.province || null,
      city: form.city || null,
      contact_person: form.contact_person || null,
      phone: form.phone || null,
      email: form.email || null,
      address: form.address || null,
      platform: currentPlatform.value,
    }

    if (currentPlatform.value === '1688') {
      payload.shop_link = form.shop_link || null
      payload.wechat_id = form.wechat_id || null
    } else if (currentPlatform.value === 'wechat') {
      payload.wechat_id = form.supplier_name  // 微信号即名称
      payload.wechat_nickname = form.wechat_nickname || null
      payload.is_dropship = form.is_dropship
    }

    if (props.supplier) {
      await suppliersApi.update(props.supplier.id, payload)
      ElMessage.success('供应商已更新')
    } else {
      const res = await suppliersApi.create(payload)
      ElMessage.success('供应商已创建')
      emit('success', res.data)
    }
    emit('update:modelValue', false)
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
```

## 调用方改造 — PurchaseDialog

### 移除前端手动 find-or-create 逻辑

当前 `PurchaseDialog` 提交时只传 `supplier_name`，**改为**：前端不需要手动 find-or-create，由后端 `createOnlinePurchase` 在写入采购单时自动按 platform + supplier_name 建立 supplier_id。

前端改动：

- 删除（或保留为可选）`createSupplierDialogVisible` 相关代码
- 保留 SupplierSearchSelect 用于线下采购
- 提交线上采购时仍传 `supplier_name` + `platform`，后端负责建立 supplier_id
- 不再向前端暴露 `/api/suppliers/find-or-create` 调用

### 采购提交示例

前端提交线上采购时**必须显式赋值所有平台字段**，避免 getattr 获取 None 导致后端校验失败：

```typescript
// PurchaseDialog 提交线上采购
if (platform.value === '1688') {
  payload.supplier_name = shopName.value      // 1688 店铺名（必填）
  payload.platform = '1688'
  payload.shop_link = linkUrl.value           // 1688 店铺链接（必填，后端校验）
  payload.wechat_id = wechatId.value || null  // 1688 微信号（选填）
  // ...
} else if (platform.value === 'wechat') {
  payload.supplier_name = wechatId.value      // 微信供应商名称 = 微信号（必填）
  payload.platform = 'wechat'
  payload.wechat_id = wechatId.value          // 微信号（必填，后端校验）
  payload.wechat_nickname = wechatNickname.value || null  // 微信昵称（选填）
  // 微信采购特有：是否支持代发
  payload.is_dropship = dropshipEnabled.value || false
  // dropshipEnabled.value 来自 PurchaseDialog 中 el-switch：微信 Tab 下勾选"支持代发"，默认值 false
  // ...
}
await purchaseApi.createOnlinePurchase(payload)
```

后端在 `createOnlinePurchase` 中自动 `find_or_create_supplier_by_name(..., platform=...)` 并写入采购单 `supplier_id`。

## 后端测试 — 两层语义

为避免 ValueError 与 HTTP 422 混用造成实现误判，测试分两层：

| 层 | 目标 | 断言方式 |
|---|---|---|
| **CRUD 单元测试** | 验证业务规则（platform 校验、shop_link 必填等） | `pytest.raises(ValueError, ...)` |
| **路由接口测试** | 验证 HTTP 响应状态码与结构化错误信息 | `assert r.status_code == 422` |

> **不要把两种测试混用**：CRUD 层抛出 ValueError，路由层负责转换为 HTTP 422。

### 后端测试 — CRUD 单元测试（ValueError 语义）

`backend/tests/test_supplier_platform.py`：

```python
@pytest.fixture
def insert_incomplete_1688(db):
    """绕过校验，直接插入不完整的 1688 历史供应商（用于测试补齐/校验逻辑）"""
    def _insert(supplier_name: str, **extra):
        supplier = SupSupplier(
            supplier_name=supplier_name,
            dept_id='S',
            supplier_code='TEST001',   # 直接插入，不触发 generate_supplier_code
            platform='1688',
            shop_link=None,             # 故意留空
            **extra
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier
    return _insert


def test_create_1688_requires_shop_link():
    payload = SupplierCreate(supplier_name='1688 店', platform='1688')
    with pytest.raises(ValueError, match='店铺链接'):
        create_supplier(db, payload)

def test_create_wechat_allows_missing_shop_link():
    payload = SupplierCreate(supplier_name='wx123', platform='wechat')
    supplier = create_supplier(db, payload)
    assert supplier.platform == 'wechat'
    assert supplier.shop_link is None

def test_response_includes_platform_fields():
    payload = SupplierCreate(supplier_name='wx123', platform='wechat', wechat_nickname='nick')
    supplier = create_supplier(db, payload)
    response = SupplierResponse.from_orm(supplier)
    assert response.platform == 'wechat'
    assert response.wechat_nickname == 'nick'

def test_find_or_create_creates_new():
    supplier, created = find_or_create_supplier_by_name(db, '1688 店 A', platform='1688', shop_link='https://...1688.com/...')
    assert created is True
    assert supplier.platform == '1688'
    assert supplier.shop_link == 'https://...1688.com/...'

def test_find_or_create_hits_existing_and_fills_missing_fields(insert_incomplete_1688):
    # 已有 1688 供应商但缺少 shop_link，本次传入 shop_link，补齐后返回
    existing = insert_incomplete_1688('1688 店 B')
    assert existing.shop_link is None
    supplier, created = find_or_create_supplier_by_name(db, '1688 店 B', platform='1688', shop_link='https://shop.1688.com')
    assert created is False
    assert supplier.id == existing.id
    assert supplier.shop_link == 'https://shop.1688.com'  # 已补齐

def test_find_or_create_hits_existing_without_shop_link_raises(insert_incomplete_1688):
    # 已有 1688 供应商缺少 shop_link，本次也没传，返回业务错误
    insert_incomplete_1688('1688 店 C')
    with pytest.raises(ValueError, match='店铺链接'):
        find_or_create_supplier_by_name(db, '1688 店 C', platform='1688')

def test_update_partial_1688_merges_and_validates(insert_incomplete_1688):
    # 部分更新：只传 supplier_name、未传 shop_link；平台已是 1688，旧值也无 shop_link → 应报错
    existing = insert_incomplete_1688('1688 店 D')
    update = SupplierUpdate(supplier_name='1688 店 D（新）')
    with pytest.raises(ValueError, match='店铺链接'):
        update_supplier(db, existing.id, update)

def test_update_fills_shop_link():
    # 部分更新：shop_link 补全（走正常校验路径，shop_link 本次传入，不会报空）
    existing = create_supplier(db, SupplierCreate(supplier_name='1688 店 E', platform='1688', shop_link='https://x.com'))
    update = SupplierUpdate(shop_link='https://shop.1688.com')
    result = update_supplier(db, existing.id, update)
    assert result.shop_link == 'https://shop.1688.com'

# --- 采购单 CRUD 校验测试 ---
# 以下测试 `create_online_purchase(db, payload)` 函数的 ValueError 行为。
# CRUD 层是唯一业务校验层：supplier_id/name 均缺失 / 跨部门 / platform 不一致 /
# platform=NULL 等校验均在 crud/purchase.create_online_purchase 中完成并抛 ValueError。
# 路由层仅负责捕获 ValueError 并转换为 HTTPException(422)，不参与业务判断。

def test_purchase_rejects_missing_supplier_id_and_name():
    # supplier_id 和 supplier_name 都没有时，采购创建应拒绝
    payload = PurchaseCreateOnline(
        dept_id='S',
        pi_id=1,
        platform='1688',
        supplier_id=None,
        supplier_name=None,
        items=[],
    )
    with pytest.raises(ValueError, match='supplier_id 或 supplier_name'):
        create_online_purchase(db, payload)

def test_purchase_rejects_null_platform_supplier():
    # 历史供应商 platform=NULL，线上采购应拒绝关联
    supplier = SupSupplier(
        supplier_name='历史供应商',
        dept_id='S',
        supplier_code='TEST002',
        platform=None,  # 故意 NULL
    )
    db.add(supplier)
    db.commit()
    payload = PurchaseCreateOnline(
        dept_id='S',
        pi_id=1,
        platform='1688',
        supplier_id=supplier.id,
        supplier_name=None,
        items=[],
    )
    with pytest.raises(ValueError, match='尚未分配平台'):
        create_online_purchase(db, payload)


def test_find_or_create_keyword_args():
    # 验证函数签名：platform 位于 dept_id 之前（必填参数不能跟在带默认值参数后面）
    supplier, created = find_or_create_supplier_by_name(
        db,
        supplier_name='关键字参数顺序测试',
        platform='wechat',  # 必填参数在前
        dept_id='S',
        shop_link=None,
        wechat_nickname='昵称',
    )
    assert created is True
    assert supplier.platform == 'wechat'
    assert supplier.wechat_nickname == '昵称'
```

### 接口级测试（路由层 HTTP 422 校验）

仅测试 CRUD 函数中抛 `ValueError` 是不够的：路由层必须把业务校验失败转成 `HTTPException(422, ...)`，前端拦截器才能拿到结构化的 `detail` 字段。下列用例使用 FastAPI `TestClient` 直接打路由，校验响应状态码与错误信息。

测试文件：`backend/tests/test_supplier_platform_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests._helpers import get_test_db  # 共享内存 SQLite / 事务回滚

client = TestClient(app)


# --- /api/suppliers/find-or-create ---

def test_find_or_create_missing_platform_returns_422():
    """缺失 platform → 422（Literal 必填字段）"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "测试店",
        "dept_id": "S",
        # platform 故意不传
    })
    assert r.status_code == 422
    assert "platform" in str(r.json())

def test_find_or_create_invalid_platform_returns_422():
    """platform 取值非法 → 422"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "测试店",
        "dept_id": "S",
        "platform": "taobao",   # 不在 {'1688','wechat','offline'}
    })
    assert r.status_code == 422

def test_find_or_create_blank_supplier_name_returns_422():
    """纯空白 supplier_name → 422"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "   ",
        "dept_id": "S",
        "platform": "1688",
    })
    assert r.status_code == 422
    assert "supplier_name" in r.json()["detail"]

def test_find_or_create_1688_missing_shop_link_returns_422():
    """platform=1688 但未传 shop_link → 422（CRUD 运行时校验，路由统一转 422）"""
    r = client.post("/api/suppliers/find-or-create", json={
        "supplier_name": "1688 缺链接店",
        "dept_id": "S",
        "platform": "1688",
        # shop_link 故意不传
    })
    assert r.status_code == 422
    assert "店铺链接" in r.json()["detail"]


# --- /api/purchase-orders/1688 (create_1688_purchase_api) ---

def test_purchase_missing_supplier_id_and_name_returns_422():
    """supplier_id 与 supplier_name 都缺失（或纯空白）→ 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        # supplier_id / supplier_name 都缺
        "items": [],
    })
    assert r.status_code == 422
    body = r.json()
    assert "supplier_id" in str(body) or "supplier_name" in str(body)

def test_purchase_blank_supplier_name_returns_422():
    """supplier_name 是纯空白字符串 → 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": None,
        "supplier_name": "   ",   # 纯空白
        "items": [],
    })
    assert r.status_code == 422

def test_purchase_supplier_id_wrong_dept_returns_422(db):
    """supplier.dept_id 与 payload.dept_id 不一致 → 422"""
    # 预设：A 部门供应商
    supplier = _seed_supplier(db, dept_id='A', platform='1688', supplier_code='SPX001')
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "B",          # 当前采购部门
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier.id,
        "items": [],
    })
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "部门" in detail
    assert supplier.dept_id in detail and "B" in detail

def test_purchase_supplier_id_null_platform_returns_422(db):
    """历史供应商 platform=NULL → 422（不允许直接关联到线上采购）"""
    supplier = _seed_supplier(db, dept_id='S', platform=None, supplier_code='SPX002')
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier.id,
        "items": [],
    })
    assert r.status_code == 422
    assert "尚未分配平台" in r.json()["detail"]

def test_purchase_supplier_id_platform_mismatch_returns_422(db):
    """供应商 platform=wechat，但采购 platform=1688 → 422"""
    supplier = _seed_supplier(db, dept_id='S', platform='wechat', supplier_code='SPX003')
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": supplier.id,
        "items": [],
    })
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "wechat" in detail and "1688" in detail

def test_purchase_unknown_supplier_id_returns_422():
    """supplier_id 不存在 → 422"""
    r = client.post("/api/purchase-orders/1688", json={
        "dept_id": "S",
        "pi_id": 1,
        "platform": "1688",
        "supplier_id": 999999,    # 不存在
        "items": [],
    })
    assert r.status_code == 422
    assert "不存在" in r.json()["detail"]


# --- /api/suppliers/{id} (update_supplier_api) ---

def test_update_platform_change_blocked_returns_422(db):
    """已存在 platform 的供应商，update 时改 platform → 422（前后端均锁定）"""
    supplier = _seed_supplier(db, dept_id='S', platform='1688', supplier_code='SPX004')
    r = client.put(f"/api/suppliers/{supplier.id}", json={
        "platform": "wechat",     # 试图变更
    })
    assert r.status_code == 422
    assert "不可修改" in r.json()["detail"]


# --- 辅助函数 ---

def _seed_supplier(db, *, dept_id: str, platform: str | None, supplier_code: str, supplier_name: str = '测试供应商'):
    """绕过校验直接插入测试用供应商"""
    from models import SupSupplier
    s = SupSupplier(
        dept_id=dept_id,
        supplier_code=supplier_code,
        supplier_name=supplier_name,
        platform=platform,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s
```

**说明**：

- 所有业务校验（部门、平台、空白名称、平台变更锁定）都必须从路由层抛出 `HTTPException(status_code=422, ...)`；如果走 `ValueError`，FastAPI 默认会返回 500，前端拦截器会判定为请求失败而非业务错误。
- 建议把"测试 status_code==422"作为合并门槛：CI 中跑 `pytest backend/tests/test_supplier_platform_api.py`，任何回归立即拦截。
- `platform` 在 `FindOrCreateSupplierRequest` 与 `PurchaseCreateOnline` 中均为 `Literal[...]` 必填，缺失会触发 Pydantic 自动 422，无需手动校验。

## 成功标准

1. 新建 1688 供应商需填写店铺链接（前后端均校验）
2. 新建微信供应商名称即微信号，必填
3. 历史供应商（platform 为 NULL）编辑时 Tabs 可切换，保存后回写 platform（NULL → 非NULL 允许）
4. 线上采购自动建立 supplier_id（后端 find-or-create 流程，按 dept_id+platform+name 精确匹配，不跨平台误复用）
5. 采购单 supplier_id 字段正确写入；传入已有 supplier_id 时后端校验平台一致性，不一致时拒绝
6. 现有线下供应商数据不受影响
7. `is_dropship` 迁移通过 server_default 自动为 False，零失败
8. 前端"供应商编号"字段禁用输入，后端自动生成并返回
9. Docker 镜像中迁移脚本位于 `/app/migrations/`，执行路径为 `python -m migrations.add_supplier_platform_fields`
10. `find_or_create_supplier_by_name` 签名与所有调用方一致（platform 为必填 str）
11. `PurchaseCreateOnline.platform` 和 `FindOrCreateSupplierRequest.platform` 均为 Literal 必填，缺失返回 422
12. 数据库唯一索引 `uq_supplier_dept_platform_name(dept_id, platform, supplier_name)` 存在，platform=NULL 时不参与约束
13. `find_or_create_supplier_by_name` 函数入口校验 `platform in ('1688', 'wechat', 'offline')`，否则 `ValueError`
14. 采购路由 supplier_id 关联校验流程：供应商存在 → dept_id 一致 → platform 非 NULL → platform 与 payload 一致；任一不满足返回 422
15. supplier_name 校验使用 `bool(payload.supplier_name and payload.supplier_name.strip())`，纯空白视为无效
16. 所有业务校验从路由层抛出 `HTTPException(422, ...)`，接口级测试覆盖（`backend/tests/test_supplier_platform_api.py`）