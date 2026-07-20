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
    dept_id: str = "S",
    contact_person: str = None,
    phone: str = None,
    address: str = None,
    platform: str,  # 必填，调用方须保证非空
    shop_link: Optional[str] = None,
    wechat_id: Optional[str] = None,
    wechat_nickname: Optional[str] = None,
    is_dropship: Optional[bool] = None,
) -> SupSupplier:
    """线上采购按 dept_id + platform + supplier_name 查找或创建供应商

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

    if platform:
        existing = get_supplier_by_name_and_platform(db, supplier_name, platform, dept_id)
        if existing:
            # 检查 1688 必填字段
            if platform == '1688' and not (existing.shop_link or shop_link):
                raise ValueError('1688 供应商必须填写店铺链接，可在供应商详情中补充后重试')
            # 补齐缺失字段并返回
            return _fill_and_return(db, existing,
                shop_link=shop_link, wechat_id=wechat_id,
                wechat_nickname=wechat_nickname, is_dropship=is_dropship)

    # 未找到，尝试创建（并发场景下可能触发唯一约束冲突）
    try:
        return _do_create_supplier(db, supplier_name, dept_id, platform,
            contact_person, phone, address, shop_link, wechat_id, wechat_nickname, is_dropship)
    except Exception as exc:
        # 并发冲突：唯一约束违反，重新查询并复用
        if 'UNIQUE constraint' in str(exc) or 'duplicate' in str(exc).lower():
            db.rollback()
            existing = get_supplier_by_name_and_platform(db, supplier_name, platform, dept_id)
            if existing:
                if platform == '1688' and not existing.shop_link and not shop_link:
                    raise ValueError('1688 供应商缺少店铺链接，可在供应商详情中补充后重试')
                return _fill_and_return(db, existing,
                    shop_link=shop_link, wechat_id=wechat_id,
                    wechat_nickname=wechat_nickname, is_dropship=is_dropship)
        raise


def _do_create_supplier(...全部参数...) -> SupSupplier:
    """实际创建供应商，内部不处理冲突"""
    _validate_platform_fields_create(...)  # 复用已有校验逻辑
    create_payload = SupplierCreate(...)
    return create_supplier(db, create_payload, dept_id)


def _fill_and_return(db, existing, **kwargs):
    """命中后补齐缺失字段并返回"""
    updated = False
    for field, value in kwargs.items():
        if value and getattr(existing, field) is None:
            setattr(existing, field, value)
            updated = True
    if updated:
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return existing
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
    # ... 现有逻辑 ...
    new_supplier = find_or_create_supplier_by_name(
        db,
        supplier_name=payload.supplier_name,
        dept_id=dept_id,
        contact_person=payload.contact_person,
        phone=payload.phone,
        address=payload.address,
        platform=payload.platform,
        shop_link=payload.shop_link,
        wechat_id=payload.wechat_id,
        wechat_nickname=payload.wechat_nickname,
        is_dropship=payload.is_dropship,
    )
    # ...
```

### `backend/routers/purchase.py`（或对应的采购路由）— 线上采购自动 find-or-create

线上采购的 `createOnlinePurchase` 入口：

```python
# 1. 传入 supplier_id 时，校验平台一致性
if payload.supplier_id:
    supplier = db.query(SupSupplier).filter(SupSupplier.id == payload.supplier_id).first()
    if not supplier:
        raise ValueError('供应商不存在')
    if supplier.platform and supplier.platform != payload.platform:
        raise ValueError(
            f'所选供应商平台为 {supplier.platform}，与本次采购平台 {payload.platform} 不一致，'
            '请重新选择或使用"新建供应商"流程'
        )
    # 一致则直接使用 supplier_id，无需 find-or-create

# 2. 未传 supplier_id 但有 supplier_name，按平台创建/查找
elif payload.supplier_name:
    # 透传 shop_link（1688 必填）、wechat_nickname 等平台字段
    supplier = find_or_create_supplier_by_name(
        db,
        supplier_name=payload.supplier_name,
        dept_id=payload.dept_id,
        platform=payload.platform,  # 必填Literal，不会为空
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

## 后端测试

`backend/tests/` 下新增 `test_supplier_platform.py`：

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
    supplier = find_or_create_supplier_by_name(db, '1688 店 A', platform='1688', shop_link='https://...1688.com/...')
    assert supplier.platform == '1688'
    assert supplier.shop_link == 'https://...1688.com/...'

def test_find_or_create_hits_existing_and_fills_missing_fields(insert_incomplete_1688):
    # 已有 1688 供应商但缺少 shop_link，本次传入 shop_link，补齐后返回
    existing = insert_incomplete_1688('1688 店 B')
    assert existing.shop_link is None
    result = find_or_create_supplier_by_name(db, '1688 店 B', platform='1688', shop_link='https://shop.1688.com')
    assert result.id == existing.id
    assert result.shop_link == 'https://shop.1688.com'  # 已补齐

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
```

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