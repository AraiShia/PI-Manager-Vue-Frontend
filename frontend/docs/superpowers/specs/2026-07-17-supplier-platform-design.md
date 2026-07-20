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

def update_supplier(db: Session, supplier_id: int, supplier_update: SupplierUpdate) -> SupSupplier:
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None
    _validate_platform_fields_update(db_supplier, supplier_update)  # 新增校验
    # ... 现有 update 逻辑 ...
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

新增参数 `platform`：

```python
def find_or_create_supplier_by_name(
    db: Session,
    supplier_name: str,
    dept_id: str = "S",
    contact_person: str = None,
    phone: str = None,
    address: str = None,
    platform: str = None,  # 新增
) -> SupSupplier:
    """线上采购按名称+platform 查找或创建供应商"""
    existing = get_supplier_by_name(db, supplier_name, dept_id)
    if existing:
        return existing

    create_payload = SupplierCreate(
        supplier_name=supplier_name,
        contact_person=contact_person or "",
        phone=phone or "",
        address=address or "",
        platform=platform,
    )
    return create_supplier(db, create_payload, dept_id)
```

### `backend/routers/supplier.py` — find-or-create 接受 platform

```python
class FindOrCreateSupplierRequest(BaseModel):
    supplier_name: str
    dept_id: Optional[str] = "S"
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    platform: Optional[str] = None  # 新增
```

调用 `find_or_create_supplier_by_name` 时传入 platform。

### `backend/routers/purchase.py`（或对应的采购路由）— 线上采购自动 find-or-create

线上采购的 `createOnlinePurchase` 入口：

```python
# 在处理 supplier_name 时：
if not payload.supplier_id and payload.supplier_name:
    # 自动按 platform + name 建立 supplier_id
    supplier = find_or_create_supplier_by_name(
        db,
        supplier_name=payload.supplier_name,
        dept_id=payload.dept_id,
        platform=payload.platform,  # '1688' / 'wechat'
        contact_person=payload.supplier_contact,
        phone=payload.supplier_phone,
    )
    if supplier:
        payload.supplier_id = supplier.id  # 写入采购单
```

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
        conn.commit()


if __name__ == "__main__":
    upgrade()
```

**Docker 容器内执行方式**：

```bash
docker exec -it <backend-container> python -m migrations.add_supplier_platform_fields
```

或在容器内：

```bash
cd /app/backend
python -m migrations.add_supplier_platform_fields
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

```typescript
// PurchaseDialog 提交线上采购
if (platform.value === '1688') {
  payload.supplier_name = shopName.value
  payload.platform = '1688'
  // ... 其他字段
} else if (platform.value === 'wechat') {
  payload.supplier_name = wechatId.value  // 微信号
  payload.platform = 'wechat'
  // ... 其他字段
}
await purchaseApi.createOnlinePurchase(payload)
```

后端在 `createOnlinePurchase` 中自动 `find_or_create_supplier_by_name(..., platform=...)` 并写入采购单 `supplier_id`。

## 后端测试

`backend/tests/` 下新增 `test_supplier_platform.py`：

```python
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

def test_find_or_create_with_platform():
    supplier = find_or_create_supplier_by_name(db, '1688 店 A', platform='1688', shop_link='https://...')
    assert supplier.platform == '1688'
```

## 成功标准

1. 新建 1688 供应商需填写店铺链接（前后端均校验）
2. 新建微信供应商名称即微信号，必填
3. 历史供应商（platform 为 NULL）编辑时 Tabs 可切换，保存后回写 platform
4. 线上采购自动建立 supplier_id（后端 find-or-create 流程）
5. 采购单 supplier_id 字段正确写入
6. 现有线下供应商数据不受影响
7. `is_dropship` 迁移通过 server_default 自动为 False，零失败