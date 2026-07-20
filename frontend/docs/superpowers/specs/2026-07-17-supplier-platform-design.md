# 供应商平台分类改造设计

## 背景与目标

当前 `SupplierFormDialog` 为通用供应商表单，字段对线上采购（1688/微信）和线下采购混用，缺少线上场景的关键字段，且所有字段一股脑展示导致表单冗余。

本次改造目标：
1. 按采购平台（1688 / 微信 / 线下）分类管理供应商
2. 各平台供应商包含差异化字段
3. 前端表单动态适应平台类型

## 数据模型

### 数据库层 — `Supplier` 模型新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `platform` | `String(20)` | 供应商平台类型：`'1688'` / `'wechat'` / `'offline'` |
| `shop_link` | `String(500)` | 1688 店铺链接 |
| `wangwang` | `String(100)` | 阿里旺旺 ID |
| `wechat_id` | `String(100)` | 微信号 |
| `wechat_nickname` | `String(100)` | 微信昵称 |
| `is_dropship` | `Boolean` | 是否支持代发（默认 false） |

### 前端类型 — `@/api/suppliers`

```typescript
export interface Supplier {
  // ... 现有字段 ...
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wangwang?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface SupplierFormPayload {
  // ... 现有字段 ...
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wangwang?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}
```

## 前端改造 — `SupplierFormDialog.vue`

### Props 新增

```typescript
const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
  /** 限定供应商平台类型，传入后 Tabs 不可切换（编辑已有供应商时） */
  platform?: '1688' | 'wechat' | 'offline'
  /** 默认平台（新建时用户可切换），默认 'offline' */
  defaultPlatform?: '1688' | 'wechat' | 'offline'
}>()
```

### 表单顶部 — 平台选择 Tabs

**新建模式**（`supplier === null`）：
- 显示 Tabs：1688 / 微信 / 线下，用户可自由切换

**编辑模式**（`supplier !== null`）：
- 读取 `supplier.platform`，Tabs 锁定为该值，不显示其他 Tab

### 各平台字段配置

**1688 供应商**：

| 字段 | 必填 | 说明 |
|------|------|------|
| 供应商编号 | 否 | 系统自动生成，可手动填 |
| 供应商名称 | 是 | — |
| 旺旺 ID | 否 | 阿里旺旺联系方式 |
| 店铺链接 | 否 | 1688 店铺 URL |
| 联系人 | 否 | — |
| 电话 | 否 | — |
| 省份/城市 | 否 | 地址（可选） |

**微信供应商**：

| 字段 | 必填 | 说明 |
|------|------|------|
| 供应商编号 | 否 | 系统自动生成 |
| 供应商名称（微信号） | 是 | 即微信号 |
| 微信昵称 | 否 | — |
| 是否支持代发 | 否 | 布尔开关，默认关闭 |
| 联系人 | 否 | — |
| 电话 | 否 | — |
| 省份/城市 | 否 | 地址（可选） |

**线下供应商**：

保持现有全部字段不变：编号、名称、省份、城市、联系人、电话、邮箱、地址。

### 表单布局

- 表单区域保持两列布局（`el-row :gutter="16"`）
- 平台 Tabs 位于表单顶部，`el-tabs` 控制
- 切换平台时，通过 `v-if` 控制各字段显隐，不重新渲染整个表单结构

### 保存逻辑

```typescript
async function save() {
  // 收集当前平台对应的字段
  const payload: SupplierFormPayload = {
    platform: currentPlatform.value,
    supplier_name: form.supplier_name,
    // 通用字段
    province: form.province || null,
    city: form.city || null,
    contact_person: form.contact_person || null,
    phone: form.phone || null,
    email: form.email || null,
    address: form.address || null,
  }

  // 根据平台追加字段
  if (currentPlatform.value === '1688') {
    payload.wangwang = form.wangwang || null
    payload.shop_link = form.shop_link || null
  } else if (currentPlatform.value === 'wechat') {
    payload.wechat_id = form.supplier_name  // 微信号即名称
    payload.wechat_nickname = form.wechat_nickname || null
    payload.is_dropship = form.is_dropship || false
  }

  // 创建/更新逻辑不变
}
```

### 搜索兼容

`SupplierSearchSelect` 下拉列表中，供应商选项展示平台标识（如小图标或标签），便于用户区分 1688 供应商和微信供应商。

## 后端改造 — `Supplier` 模型

新增数据库字段（ Alembic migration）：

```python
# 迁移文件
sa.Column('platform', sa.String(20), nullable=True)  # '1688' / 'wechat' / 'offline'
sa.Column('shop_link', sa.String(500), nullable=True)
sa.Column('wangwang', sa.String(100), nullable=True)
sa.Column('wechat_id', sa.String(100), nullable=True)
sa.Column('wechat_nickname', sa.String(100), nullable=True)
sa.Column('is_dropship', sa.Boolean, default=False, nullable=False)
```

`suppliersApi.create` / `suppliersApi.update` 自动透传新增字段。

## 调用方改造

### PurchaseDialog — 传入平台类型

```vue
<SupplierSearchSelect
  v-model="form.supplier"
  :current-name="form.supplier_name"
  @select="onSupplierSelect"
  @clear="onSupplierClear"
/>

<!-- 新建供应商时，传入当前采购平台 -->
<SupplierFormDialog
  v-model="newSupplierDialogVisible"
  :supplier="null"
  :default-platform="purchasePlatform"
  @success="onNewSupplierCreated"
/>
```

其中 `purchasePlatform` 来自 `el-tabs` 选中的采购类型（`'1688'` / `'wechat'` / `'offline'`）。

## 实现计划

### 阶段一：后端数据模型
1. 编写 Alembic 迁移文件添加新字段
2. 更新 `Supplier` Pydantic Schema
3. 测试 CRUD 接口透传新字段

### 阶段二：前端类型和 API
1. 更新 `@/api/suppliers` 的 `Supplier` / `SupplierFormPayload` 类型
2. `suppliersApi.create/update` 透传新字段

### 阶段三：SupplierFormDialog 重构
1. 新增 `platform` / `defaultPlatform` props
2. 表单顶部添加 `el-tabs` 平台选择
3. 各平台字段 `v-if` 动态展示
4. 更新 `emptyForm()` 和表单重置逻辑
5. 更新 `save()` 收集平台字段

### 阶段四：搜索组件适配
1. `SupplierSearchSelect` 下拉选项显示平台标识

### 阶段五：PurchaseDialog 集成
1. 采购类型 Tabs 联动 `default-platform` prop
2. 确保新建供应商时传入正确平台

## 成功标准

1. 新建 1688 供应商可填写旺旺 ID 和店铺链接，并保存到数据库
2. 新建微信供应商可填写微信号、昵称、代发标识，并保存到数据库
3. 编辑已有供应商时，Tabs 锁定为该供应商的平台类型
4. 供应商搜索下拉列表可区分不同平台的供应商
5. 现有线下供应商数据不受影响
