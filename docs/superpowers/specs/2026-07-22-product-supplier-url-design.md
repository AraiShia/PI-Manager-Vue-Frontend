# 产品-供应商-URL 关联设计

## 1. 背景与目标

当前系统中：
- `sup_supplier.shop_link` — 一个供应商对应一个店铺链接
- `pi_item.shop_url` — PI 产品行的采购链接（快照）
- `po_1688_purchase.product_url` — 历史采购记录中的产品链接

**问题：** 同一供应商的不同产品可能对应不同的 1688 链接，当前无法区分和管理。

**目标：** 建立「产品-供应商-URL」的多对一关联，支持：
- 采购成功后自动记录 URL 到历史
- 选择供应商后拉取该产品的历史 URL 下拉
- 在 `ProductEditDialog` 和 `PurchaseDialog` 中选择/填入 URL
- 未来同产品下单时自动回填

---

## 2. 数据模型

### 2.1 新增表 `prd_product_supplier_url`

```python
class PrdProductSupplierUrl(Base):
    __tablename__ = "prd_product_supplier_url"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    product_id    = Column(Integer, ForeignKey("prd_customer_product.id"), nullable=False)
    supplier_id   = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
    supplier_name = Column(String(200), nullable=False)   # 历史快照
    url           = Column(String(500), nullable=False)
    display_name  = Column(String(100), nullable=True)
    is_default    = Column(Boolean, default=False)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", "url", name="ux_product_supplier_url"),
        Index("ix_product_supplier_url_supplier", "supplier_id"),
        Index("ix_product_supplier_url_product", "product_id"),
    )
```

### 2.2 `po_1688_purchase` 新增 `supplier_id` 字段

```python
supplier_id = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
```

**采购链路贯穿 supplier_id：**
- `Po1688PurchaseItem` 新增 `supplier_id: Optional[int]`
- 路由层 `create_1688_purchase_api` 调用 `resolve_online_supplier` 后将 `supplier_id` 注入到每个 `Po1688PurchaseItem`
- `create_1688_purchase_batch()` 在创建 `Po1688Purchase` 时赋值 `supplier_id`

### 2.3 数据库迁移

**新表创建：**
```sql
CREATE TABLE prd_product_supplier_url (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  supplier_id INTEGER,
  supplier_name VARCHAR(200) NOT NULL,
  url VARCHAR(500) NOT NULL,
  display_name VARCHAR(100),
  is_default BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(product_id, supplier_id, url)
);
CREATE INDEX ix_psu_supplier ON prd_product_supplier_url(supplier_id);
CREATE INDEX ix_psu_product ON prd_product_supplier_url(product_id);
```

**`po_1688_purchase` 迁移：**
```sql
ALTER TABLE po_1688_purchase ADD COLUMN supplier_id INTEGER REFERENCES sup_supplier(id);
UPDATE po_1688_purchase
SET supplier_id = (
    SELECT id FROM sup_supplier
    WHERE sup_supplier.supplier_name = po_1688_purchase.supplier_name
    LIMIT 1
)
WHERE supplier_id IS NULL;
```

**历史数据导入（新表）：**

```sql
-- 从 po_1688_purchase 把已有历史链接导入新表
-- 同一 (product_id, supplier_id, url) 重复时保留最早的一条
-- 最近一条设为 is_default=1
INSERT INTO prd_product_supplier_url
    (product_id, supplier_id, supplier_name, url, is_default, created_at)
SELECT
    p.product_id,
    p.supplier_id,
    p.supplier_name,
    p.product_url,
    -- 同一 (product_id, supplier_id, url) 中最新一条置为默认
    CASE WHEN p.created_at = (
        SELECT MAX(p2.created_at)
        FROM po_1688_purchase p2
        WHERE p2.product_id = p.product_id
          AND COALESCE(p2.supplier_id, -1) = COALESCE(p.supplier_id, -1)
          AND p2.product_url = p.product_url
    ) THEN 1 ELSE 0 END,
    p.created_at
FROM po_1688_purchase p
WHERE p.product_url IS NOT NULL AND p.product_url <> '';

-- 用唯一索引去重（如有重复则保留最早）
DELETE FROM prd_product_supplier_url
WHERE id NOT IN (
    SELECT MIN(id) FROM prd_product_supplier_url
    GROUP BY product_id, supplier_id, url
);
```

**注意：** 如果 supplier_id 为 NULL，按 `(product_id, -1, url)` 分组；唯一索引允许 supplier_id 为 NULL（SQLite 默认允许多个 NULL）。

---

## 3. API 设计

### 3.1 路由 `/api/product-supplier-urls`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/product-supplier-urls` | GET | 查询列表（按 `product_id` + `supplier_id` 过滤，缺 `supplier_id` 时按 `supplier_name` fallback） |
| `/api/product-supplier-urls` | POST | 创建 URL（重复返回已有记录，`is_default` 升降级规则见 5.2） |
| `/api/product-supplier-urls/{id}` | PUT | 更新 URL 记录，URL 冲突返回 409 |
| `/api/product-supplier-urls/{id}` | DELETE | 删除 URL 记录 |

### 3.2 GET 查询参数与规则

```
GET /api/product-supplier-urls?product_id=123&supplier_id=456
GET /api/product-supplier-urls?product_id=123&supplier_name=xxx  # fallback
```

**查询优先级：**
1. 优先按 `supplier_id` 查询
2. 旧数据 `supplier_id` 为 NULL，按 `supplier_name` 查询

**返回：** 按 `is_default DESC, created_at DESC` 排序

### 3.3 POST 请求体

```json
{
  "product_id": 123,
  "supplier_id": 456,
  "supplier_name": "供应商A",
  "url": "https://detail.1688.com/item/123.html",
  "display_name": "店铺A-链接1",
  "is_default": false
}
```

**约束：**
- `url` 长度 ≤ 500，必须以 `http://` 或 `https://` 开头
- `product_id`、`supplier_id` 必须存在
- 同一 `(product_id, supplier_id, url)` 重复时：
  - 返回 200 + 已有记录（不重复创建）
  - 若请求中 `is_default=true`，**仍将其升级为默认**

### 3.4 POST 返回 200/201 语义

| 情况 | 状态码 |
|------|--------|
| 新建 | 201 |
| 重复（含 is_default 升级） | 200 |

### 3.5 PUT 请求体

```json
{
  "url": "https://detail.1688.com/item/456.html",
  "display_name": "新链接",
  "is_default": false
}
```

**约束：** URL 与同 `(product_id, supplier_id)` 下其他记录冲突时返回 409。

### 3.6 DELETE

无需权限校验，由前端调用。

---

## 4. `is_default` 业务规则

| 场景 | 行为 |
|------|------|
| 新建 URL（POST） | `is_default` 由前端指定；设为 `true` 时自动取消同产品同供应商其他默认 |
| 重复 POST + `is_default=true` | 把已存在记录升级为默认 |
| 删除默认 URL | 若有其他 URL，**最新创建**的一条自动成为默认；若无其他 URL，允许空 |
| 选择 URL（前端） | 不自动改 `is_default` |

实现：
```python
# POST 时升级默认
if data.is_default:
    db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == data.product_id,
        PrdProductSupplierUrl.supplier_id == data.supplier_id,
        PrdProductSupplierUrl.id != url.id,
    ).update({"is_default": False})

# DELETE 默认后修复孤儿默认
if url.is_default:
    db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == url.product_id,
        PrdProductSupplierUrl.supplier_id == url.supplier_id,
        PrdProductSupplierUrl.id != url_id,
    ).update({"is_default": False})
    next_default = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == url.product_id,
        PrdProductSupplierUrl.supplier_id == url.supplier_id,
        PrdProductSupplierUrl.id != url_id,
    ).order_by(PrdProductSupplierUrl.created_at.desc()).first()
    if next_default:
        next_default.is_default = True
```

---

## 5. 前端改动

### 5.1 API 层

新增 `frontend/src/api/productSupplierUrls.ts`：
- `list(productId, supplierId?, supplierName?)` — 查询 URL 列表
- `create(payload)` — 创建 URL
- `update(id, payload)` — 更新 URL（409 错误抛出供前端处理）
- `remove(id)` — 删除 URL

### 5.2 `ProductEditDialog` 改动

**供应商链接字段（第 357-364 行）：**

#### URL 来源优先级

处理顺序（高优先级覆盖低优先级，但只在用户未手动填入时）：

| 优先级 | 来源 |
|--------|------|
| 1 | 当前 `pi_item.shop_url`（已有值） |
| 2 | 该 `(product_id, supplier_id)` 的默认 URL（`is_default=true`） |
| 3 | 同一 product_id + supplier_name 的最新 URL（fallback） |
| 4 | `sup_supplier.shop_link`（仅在用户通过 `SupplierSearchSelect` 选了带 shop_link 的供应商时） |
| 5 | 空 |

#### 实现

- `SupplierSearchSelect` 选择供应商后：
  - 查询 `prd_product_supplier_url`（按 `product_id + supplier_id`）
  - 将 URL 列表作为下拉展示（`el-select + allow-create`）
  - 用户可选择已有 URL 或手动输入新 URL
  - 选/填后：
    - 调用 `api.create()` 持久化（URL 重复返回已有，不报错）
    - `saveField('shop_url', form.shop_url)` 写入 `pi_item.shop_url`
  - 切换供应商时重新加载 URL 列表

### 5.3 `PurchaseDialog` 改动

**多产品场景（关键修正）：**

`PurchaseDialog` 支持多产品采购，每行 `item.link` 已存在但不展示。本设计让**每行可独立选择 URL**。

#### 表格改造（第 12-47 行附近）

在产品表格的「总金额」前新增一列「1688链接」：

```vue
<el-table-column label="1688链接" width="220">
  <template #default="{ row, $index }">
    <el-select
      v-model="row.link"
      filterable
      allow-create
      default-first-option
      placeholder="选择或输入链接"
      size="small"
      :disabled="row._locked"
      @change="(url: string) => onItemUrlChange($index, url)"
    >
      <el-option
        v-for="u in row._urlOptions"
        :key="u.id || u.url"
        :label="u.display_name || u.url"
        :value="u.url"
      />
    </el-select>
  </template>
</el-table-column>
```

#### 数据加载

在 `loadInitialPrices()` 中，每个产品行加载 `(product_id, supplier_id)` 的 URL 列表 → 存入 `row._urlOptions`：

```typescript
// 选中供应商后触发 reload（先有供应商才能查 URL）
async function reloadAllUrls() {
  const supplier = pendingSupplierState.supplier || selectedSupplier
  if (!supplier) return
  for (const row of items.value) {
    if (!row.product_id) continue
    const res = await productSupplierUrlsApi.list(row.product_id, supplier.id, supplier.supplier_name)
    row._urlOptions = res.data || []
  }
}
```

#### 提交逻辑

在 `createOnlinePurchase` 调用后，对每个有 URL 的 item 调用 `productSupplierUrlsApi.create()`：

```typescript
// 提交成功后，对每个非空 URL 写入历史
if (result.success && platform.value === '1688') {
  const supplierId = pendingSupplierState.supplier?.id
  const supplierName = pendingSupplierState.supplier?.supplier_name
  for (const item of items.value) {
    if (!item.link || !item.product_id) continue
    await productSupplierUrlsApi.create({
      product_id: item.product_id,
      supplier_id: supplierId,
      supplier_name: supplierName,
      url: item.link,
    }).catch(console.warn)
  }
}
```

#### 顶层 `linkUrl`（顶层供应商联系字段）

仍保留用于非表格行场景（如主店铺链接），不参与每行 URL。

---

## 6. 供应商链接填充规则

**避免竞态：** `SupplierSearchSelect` 选择供应商后，先查询 URL 历史→选择默认值→异步加载期间不要用 `supplier.shop_link` 覆盖。

具体逻辑：
1. 用户选择供应商 `S`
2. 立即触发 `loadSupplierUrls(product_id, S.id)`
3. 若 `form.shop_url` 已有值（用户已填），不覆盖
4. 若 `form.shop_url` 为空：
   - 默认 URL（`is_default=true`） → 填入
   - 否则最新 URL → 填入
   - 否则 `S.shop_link` → 填入（仅 1688 platform）
   - 否则留空
5. URL 下拉显示选项 + allow-create

---

## 7. 事务边界（关键）

**线上采购流程事务：**

```
Route: create_1688_purchase_api(purchase_data)
    try:
        supplier_id = resolve_online_supplier(...)         # 仅 flush
        batch = ...
        created_records = create_1688_purchase_batch(...) # 仅 flush，不 commit
        # ↑ 现在 URL 历史写入逻辑内联在这里，也仅 flush
        po_payload = ...
        purchase_orders = create_grouped_purchase_orders(...)  # 仅 flush
        db.commit()                                        # 唯一提交点
```

**改动：**
- `create_1688_purchase_batch()` 移除内部 `db.commit()`，改为 `db.flush()`，返回 SQLAlchemy 对象
- URL 历史写入放在批处理内（同样 flush）
- 路由层 `db.commit()` 是唯一提交点

如果任一数据库操作失败，整个事务回滚，包括 URL 历史和采购单。

---

## 8. 范围

| 功能 | 范围 |
|------|------|
| 新表 + 迁移（含历史数据导入） | ✅ 本次 |
| CRUD API（含 is_default 闭环） | ✅ 本次 |
| `supplier_id` 贯穿采购链路 | ✅ 本次 |
| 采购成功后写入 URL 历史（同事务） | ✅ 本次 |
| `ProductEditDialog` URL 下拉 | ✅ 本次 |
| `PurchaseDialog` 每行 URL 下拉 | ✅ 本次 |
| 批量导入自动回填 | ❌ 后续 |
