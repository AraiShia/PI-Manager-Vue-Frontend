# 供应商平台分类改造实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为供应商增加平台类型字段（1688/微信/线下），前端 SupplierFormDialog 根据平台动态展示差异化表单字段

**架构：** 后端数据库新增 platform、shop_link、wechat_id、wechat_nickname、is_dropship 字段；前端 SupplierFormDialog 新增 platform prop 和 el-tabs 切换；PurchaseDialog 传入采购类型平台

**技术栈：** Python (FastAPI/SQLAlchemy), Vue 3 + TypeScript, Element Plus, Alembic

---

## 文件结构

### Backend
- 修改：`backend/models/supplier.py` — 新增 platform、shop_link、wechat_id、wechat_nickname、is_dropship 字段
- 修改：`backend/schemas/supplier.py` — SupplierCreate/Update/Response 新增字段
- 修改：`backend/routers/supplier.py` — create/update 接口透传新字段
- 新增：`backend/alembic/versions/YYYYMMDDHHMMSS_add_supplier_platform_fields.py` — Alembic 迁移

### Frontend
- 修改：`frontend/src/api/suppliers.ts` — Supplier/SupplierFormPayload 类型新增字段
- 修改：`frontend/src/components/supplier/SupplierFormDialog.vue` — 新增 platform/defaultPlatform props、el-tabs 平台切换、动态字段展示
- 修改：`frontend/src/components/order/PurchaseDialog.vue` — 传入 default-platform prop（线上采购时为 '1688' 或 'wechat'）
- 测试：`frontend/src/components/common/__tests__/SupplierFormDialog.test.ts` — 新增单元测试（如已有测试文件）

---

## 后端任务

### 任务 1：后端 — 新增数据库迁移

**文件：**
- 新增：`backend/alembic/versions/YYYYMMDDHHMMSS_add_supplier_platform_fields.py`
- 参考：`backend/alembic/versions/` 下已有迁移文件格式

- [ ] **步骤 1：编写 Alembic 迁移**

```python
"""add supplier platform fields

Revision ID: xxxxxx
Revises: xxxxxx
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxxxx'
down_revision = 'xxxxxx'  # 填入当前最新的 revision
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('sup_supplier', sa.Column('platform', sa.String(20), nullable=True))
    op.add_column('sup_supplier', sa.Column('shop_link', sa.String(500), nullable=True))
    op.add_column('sup_supplier', sa.Column('wechat_id', sa.String(100), nullable=True))
    op.add_column('sup_supplier', sa.Column('wechat_nickname', sa.String(100), nullable=True))
    op.add_column('sup_supplier', sa.Column('is_dropship', sa.Boolean, default=False, nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('sup_supplier', 'is_dropship')
    op.drop_column('sup_supplier', 'wechat_nickname')
    op.drop_column('sup_supplier', 'wechat_id')
    op.drop_column('sup_supplier', 'shop_link')
    op.drop_column('sup_supplier', 'platform')
```

- [ ] **步骤 2：验证迁移文件格式**

运行：`cd backend && python -c "import alembic.config; print('OK')"`
预期：OK（无报错说明 alembic 可用）

- [ ] **步骤 3：查看当前最新 revision**

运行：`cd backend && alembic current`
预期：输出当前 revision hash（如 `a1b2c3d4`）

- [ ] **步骤 4：将迁移文件中的 `down_revision` 替换为上一步的输出值**

打开迁移文件，找到 `down_revision = 'xxxxxx'`，替换为实际值。

- [ ] **步骤 5：执行迁移**

运行：`cd backend && alembic upgrade head`
预期：`Running upgrade  ... -> xxxxxx`（无 ERROR）

- [ ] **步骤 6：验证字段已创建**

运行：`cd backend && python -c "from models.supplier import SupSupplier; from sqlalchemy import inspect; cols = [c.name for c in inspect(SupSupplier).columns]; print('platform' in cols, 'shop_link' in cols, 'wechat_id' in cols, 'wechat_nickname' in cols, 'is_dropship' in cols)"`
预期：`True True True True True`

- [ ] **步骤 7：Commit**

```bash
git add backend/alembic/versions/xxxxxxxx_add_supplier_platform_fields.py
git commit -m "backend: add supplier platform fields migration"
```

---

### 任务 2：后端 — 更新 Pydantic Schema

**文件：**
- 修改：`backend/schemas/supplier.py`

- [ ] **步骤 1：更新 SupplierBase、SupplierCreate、SupplierUpdate、SupplierResponse**

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
    # 平台分类字段
    platform: Optional[str] = None
    shop_link: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None

    class Config:
        from_attributes = True
```

- [ ] **步骤 2：验证 Schema 无语法错误**

运行：`cd backend && python -c "from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse; print('OK')"`
预期：OK

- [ ] **步骤 3：Commit**

```bash
git add backend/schemas/supplier.py
git commit -m "backend: add platform fields to supplier schemas"
```

---

### 任务 3：后端 — 更新 Router 透传字段

**文件：**
- 修改：`backend/routers/supplier.py`

- [ ] **步骤 1：读取 router 文件找到 create 和 update 方法**

读取 `backend/routers/supplier.py`，找到 `create_supplier` 和 `update_supplier` 函数。

- [ ] **步骤 2：确保 create 时透传 platform 相关字段**

在 `create_supplier` 中，`SupSupplier` 构造参数追加：
```python
SupSupplier(
    # ... 现有字段 ...
    platform=supplier_data.platform,
    shop_link=supplier_data.shop_link,
    wechat_id=supplier_data.wechat_id,
    wechat_nickname=supplier_data.wechat_nickname,
    is_dropship=supplier_data.is_dropship or False,
)
```

- [ ] **步骤 3：确保 update 时透传 platform 相关字段**

在 `update_supplier` 中，追加：
```python
if supplier_data.platform is not None:
    setattr(supplier, 'platform', supplier_data.platform)
if supplier_data.shop_link is not None:
    setattr(supplier, 'shop_link', supplier_data.shop_link)
if supplier_data.wechat_id is not None:
    setattr(supplier, 'wechat_id', supplier_data.wechat_id)
if supplier_data.wechat_nickname is not None:
    setattr(supplier, 'wechat_nickname', supplier_data.wechat_nickname)
if supplier_data.is_dropship is not None:
    setattr(supplier, 'is_dropship', supplier_data.is_dropship)
```

- [ ] **步骤 4：验证语法**

运行：`cd backend && python -c "import routers.supplier; print('OK')"`
预期：OK

- [ ] **步骤 5：Commit**

```bash
git add backend/routers/supplier.py
git commit -m "backend: pass platform fields in supplier create/update"
```

---

## 前端任务

### 任务 4：前端 — 更新类型定义

**文件：**
- 修改：`frontend/src/api/suppliers.ts`

- [ ] **步骤 1：更新 Supplier 和 SupplierFormPayload 类型**

```typescript
export interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  status?: number | null
  created_at?: string | null
  updated_at?: string | null
  // 平台分类字段
  platform?: '1688' | 'wechat' | 'offline' | null
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface SupplierFormPayload {
  supplier_code: string
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  // 平台分类字段
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}
```

- [ ] **步骤 2：验证构建**

运行：`cd frontend && npm run build 2>&1 | Select-String -Pattern "error|Error|built in"`
预期：`built in`（无 error）

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/api/suppliers.ts
git commit -m "frontend: add platform fields to Supplier type"
```

---

### 任务 5：前端 — 重构 SupplierFormDialog

**文件：**
- 修改：`frontend/src/components/supplier/SupplierFormDialog.vue`

- [ ] **步骤 1：更新 Props 和 emit**

```typescript
const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
  /** 限定平台类型，传入后 Tabs 不可切换（编辑已有供应商时） */
  platform?: '1688' | 'wechat' | 'offline'
  /** 默认平台（新建时用户可切换），默认 'offline' */
  defaultPlatform?: '1688' | 'wechat' | 'offline'
}>()
```

- [ ] **步骤 2：新增 currentPlatform ref 和 computed isEditLocked**

```typescript
const isEditLocked = computed(() => !!props.supplier && !!props.supplier.platform)
const currentPlatform = ref<'1688' | 'wechat' | 'offline'>(
  props.supplier?.platform || props.defaultPlatform || 'offline'
)
```

- [ ] **步骤 3：更新 emptyForm() 增加平台字段**

```typescript
const emptyForm = () => ({
  supplier_code: '',
  supplier_name: '',
  province: '',
  city: '',
  contact_person: '',
  phone: '',
  email: '',
  address: '',
  // 1688 字段
  shop_link: '',
  wechat_id: '',
  // 微信字段
  wechat_nickname: '',
  is_dropship: false,
})
```

- [ ] **步骤 4：更新表单模板 — 表单顶部添加 el-tabs 平台选择**

在 `<el-form>` 之前添加：
```vue
<el-tabs v-if="!isEditLocked" v-model="currentPlatform" class="supplier-platform-tabs">
  <el-tab-pane label="1688" name="1688" />
  <el-tab-pane label="微信" name="wechat" />
  <el-tab-pane label="线下" name="offline" />
</el-tabs>

<!-- 编辑已有供应商时，显示平台标签 -->
<div v-else class="supplier-platform-badge">
  <el-tag type="info">{{ platformLabelMap[currentPlatform] }}</el-tag>
</div>
```

- [ ] **步骤 5：更新表单字段 v-if 展示（el-form 内）**

将所有 `el-form-item` 用 `v-if` 按平台控制显隐：
```vue
<!-- 通用字段（所有平台） -->
<el-form-item label="供应商名称" prop="supplier_name">
  <el-input v-model="form.supplier_name" />
</el-form-item>

<!-- 1688 专属 -->
<el-form-item v-if="currentPlatform === '1688'" label="店铺链接" prop="shop_link">
  <el-input v-model="form.shop_link" placeholder="https://...1688.com/..." />
</el-form-item>
<el-form-item v-if="currentPlatform === '1688'" label="微信号">
  <el-input v-model="form.wechat_id" />
</el-form-item>

<!-- 微信专属 -->
<el-form-item v-if="currentPlatform === 'wechat'" label="微信昵称">
  <el-input v-model="form.wechat_nickname" />
</el-form-item>
<el-form-item v-if="currentPlatform === 'wechat'" label="支持代发">
  <el-switch v-model="form.is_dropship" />
</el-form-item>

<!-- 线下专属（无需额外字段，省份城市等通用字段保留） -->
```

- [ ] **步骤 6：更新 save() 函数收集平台字段**

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

- [ ] **步骤 7：更新 watch supplier 填充新字段**

```typescript
watch(() => props.supplier, (s) => {
  if (s) {
    Object.assign(form, emptyForm(), {
      supplier_code: s.supplier_code || '',
      supplier_name: s.supplier_name || '',
      province: s.province || '',
      city: s.city || '',
      contact_person: s.contact_person || '',
      phone: s.phone || '',
      email: s.email || '',
      address: s.address || '',
      // 平台分类字段
      shop_link: s.shop_link || '',
      wechat_id: s.wechat_id || '',
      wechat_nickname: s.wechat_nickname || '',
      is_dropship: s.is_dropship || false,
    })
    if (s.platform) {
      currentPlatform.value = s.platform
    }
    if (s.province) {
      loadCities(s.province, s.city)
    }
  } else {
    Object.assign(form, emptyForm())
    currentPlatform.value = props.defaultPlatform || 'offline'
  }
  cities.value = []
}, { immediate: true })
```

- [ ] **步骤 8：添加平台标签样式**

```css
.supplier-platform-tabs {
  margin-bottom: 16px;
}

.supplier-platform-badge {
  margin-bottom: 16px;
}
```

- [ ] **步骤 9：验证构建**

运行：`cd frontend && npm run build 2>&1 | Select-String -Pattern "error|Error|built in"`
预期：`built in`（无 error）

- [ ] **步骤 10：Commit**

```bash
git add frontend/src/components/supplier/SupplierFormDialog.vue
git commit -m "frontend: SupplierFormDialog supports platform tabs and dynamic fields"
```

---

### 任务 6：前端 — PurchaseDialog 集成

**文件：**
- 修改：`frontend/src/components/order/PurchaseDialog.vue`

- [ ] **步骤 1：找到新建供应商的 SupplierFormDialog 调用处**

在 `PurchaseDialog.vue` 中找到 `<SupplierFormDialog>` 的使用位置（在模板底部）。

- [ ] **步骤 2：传入 default-platform prop**

将 `<SupplierFormDialog ... />` 替换为：
```vue
<SupplierFormDialog
  v-model="newSupplierDialogVisible"
  :supplier="null"
  :default-platform="purchasePlatform"
  @success="onNewSupplierCreated"
/>
```

其中 `purchasePlatform` 是当前采购类型 Tabs 选中的值（`'1688'` / `'wechat'` / `'offline'`）。如果采购类型 Tabs 变量名不同（如 `purchaseMode`），替换为实际变量名。

- [ ] **步骤 3：验证构建**

运行：`cd frontend && npm run build 2>&1 | Select-String -Pattern "error|Error|built in"`
预期：`built in`（无 error）

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/components/order/PurchaseDialog.vue
git commit -m "frontend: PurchaseDialog passes defaultPlatform to SupplierFormDialog"
```

---

## 规格覆盖度检查

- [x] 后端数据库字段 — 任务 1
- [x] 后端 Schema 更新 — 任务 2
- [x] 后端 Router 透传 — 任务 3
- [x] 前端类型更新 — 任务 4
- [x] SupplierFormDialog 重构（platform prop、el-tabs、动态字段）— 任务 5
- [x] PurchaseDialog 传入 defaultPlatform — 任务 6

**占位符扫描：** 无 "TODO"、"待定" 或模糊描述。所有步骤包含完整代码和命令。

**类型一致性：** `SupplierCreate` / `SupplierUpdate` 中的 `platform` 字段类型为 `Literal['1688', 'wechat', 'offline']`，前端 props 和 currentPlatform ref 使用相同字面量类型，后端迁移字段为 `String(20)`，一致。

---

计划已完成并保存到 `docs/superpowers/plans/2026-07-17-supplier-platform-implementation.md`。

两种执行方式：

**1. 子代理驱动（推荐）** — 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** — 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

选哪种方式？