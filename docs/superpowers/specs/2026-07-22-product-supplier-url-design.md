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

**历史数据导入（新表，v4 修订）：**

```sql
-- v4 修订要点：
--   1. 默认项判断改用最早一条（保留行）= 同组最新一条 created_at 的版本
--   2. supplier_name 为空的历史记录被过滤
--   3. supplier_id 仅按 dept_id + supplier_name + platform='1688' 精确匹配

-- 4. 历史 URL 导入新表
INSERT INTO prd_product_supplier_url
    (product_id, supplier_id, supplier_name, url, is_default, created_at)
SELECT * FROM (
    SELECT
        p.product_id,
        p.supplier_id,
        p.supplier_name,
        p.product_url,
        -- v4 修订：用 lastest_created_at 判断
        CASE WHEN p.created_at = p.latest_created_at THEN 1 ELSE 0 END,
        p.created_at
    FROM (
        SELECT
            p1.product_id,
            p1.supplier_id,
            p1.supplier_name,
            p1.product_url,
            p1.created_at,
            p1.id,
            -- 最早一条保留（受 SUPPLIER_GROUPPER ATION 分组）
            ROW_NUMBER() OVER (
                PARTITION BY
                    p1.product_id,
                    COALESCE(p1.supplier_id, 0),
                    p1.product_url
                ORDER BY p1.created_at ASC, p1.id ASC
            ) AS row_num_asc,
            -- 同组最新 created_at（同一组其他记录共享）
            MAX(p1.created_at) OVER (
                PARTITION BY
                    p1.product_id,
                    COALESCE(p1.supplier_id, 0),
                    p1.product_url
            ) AS latest_created_at
        FROM po_1688_purchase p1
        WHERE p1.product_url IS NOT NULL AND p1.product_url <> ''
          AND p1.supplier_name IS NOT NULL AND p1.supplier_name <> ''
    ) p
    WHERE p.row_num_asc = 1   -- 只插入同组最早一条
) final;
```

**注释：**

| 决策 | 理由 |
|------|------|
| 同一 `(product_id, supplier_id, url)` 保留最早一条 | 唯一索引 + 历史可追溯 |
| 默认项 = 同组最新一条 created_at | 用户最常使用最新链接为默认 |
| `MAX(...) OVER (PARTITION BY ...)` 获取同组最新时间 | 避免同一 URL 出现在多行记录中时 `is_default` 状态不一致 |
| `COALESCE(supplier_id, 0)` 解决 NULL 分组 | SQLite 唯一索引允许多个 NULL，将 NULL 映射为 0 让分组生效 |
| 过滤 supplier_name 为空的记录 | 新表 supplier_name NOT NULL；导不进去的空记录跳过并记数 |

**时间相同的情况：** `MAX(created_at)` 不能区分同时间多条；后续用 `id DESC` 决定谁是"最新"，引入额外列 `max_id_per_group`：

```sql
MAX(p1.id) OVER (
    PARTITION BY p1.product_id, COALESCE(p1.supplier_id, 0), p1.product_url
) AS max_id_in_group
```

判断：
```sql
CASE WHEN p.id = p.max_id_in_group THEN 1 ELSE 0 END  -- is_default
```

这样保证 `created_at` 相同时仍确定性的、最新的（id 最大）一条为默认。

**完整最终 SQL：**

```sql
INSERT INTO prd_product_supplier_url
    (product_id, supplier_id, supplier_name, url, is_default, created_at)
SELECT * FROM (
    SELECT
        p.product_id,
        p.supplier_id,
        p.supplier_name,
        p.product_url,
        CASE WHEN p.id = p.max_id_in_group THEN 1 ELSE 0 END,
        p.created_at
    FROM (
        SELECT
            p1.product_id,
            p1.supplier_id,
            p1.supplier_name,
            p1.product_url,
            p1.created_at,
            p1.id,
            ROW_NUMBER() OVER (
                PARTITION BY p1.product_id, COALESCE(p1.supplier_id, 0), p1.product_url
                ORDER BY p1.created_at ASC, p1.id ASC
            ) AS row_num_asc,
            MAX(p1.id) OVER (
                PARTITION BY p1.product_id, COALESCE(p1.supplier_id, 0), p1.product_url
            ) AS max_id_in_group
        FROM po_1688_purchase p1
        WHERE p1.product_url IS NOT NULL AND p1.product_url <> ''
          AND p1.supplier_name IS NOT NULL AND p1.supplier_name <> ''
    ) p
    WHERE p.row_num_asc = 1
) final;
```

**供应商关联回填（只有精确匹配，不留宽松默认）：**

```sql
-- 仅有精细版本：无 dept_id+platform+supplier_name 完全匹配时 supplier_id 保持 NULL
UPDATE po_1688_purchase
SET supplier_id = (
    SELECT id FROM sup_supplier
    WHERE sup_supplier.supplier_name = po_1688_purchase.supplier_name
      AND sup_supplier.dept_id = po_1688_purchase.dept_id
      AND sup_supplier.platform = '1688'
    LIMIT 1
)
WHERE supplier_id IS NULL;
```

迁移完成后记录统计：
```sql
SELECT COUNT(*) AS total FROM po_1688_purchase;
SELECT COUNT(*) AS matched FROM po_1688_purchase WHERE supplier_id IS NOT NULL;
SELECT COUNT(*) AS unmatched FROM po_1688_purchase WHERE supplier_id IS NULL;
SELECT COUNT(*) AS history_urls_imported FROM prd_product_supplier_url;
SELECT COUNT(*) AS skipped_due_to_null_supplier_name
FROM po_1688_purchase WHERE product_url IS NOT NULL AND product_url <> ''
  AND (supplier_name IS NULL OR supplier_name = '');
```

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
- **新数据强制要求 `supplier_id`（不可为 NULL）**；只有迁移导入的旧数据允许 `supplier_id=NULL`
- `product_id` 必须存在
- `supplier_id` 必须存在
- 同一 `(product_id, supplier_id, url)` 重复时：
  - 返回 200 + 已有记录（不重复创建）
  - 若请求中 `is_default=true`，**仍将其升级为默认**

### 3.3.1 supplier_id 一致性约束

| 场景 | supplier_id 处理 |
|------|------------------|
| 新建 URL（POST） | 必填，传 NULL 返回 422 |
| 迁移导入的旧数据 | 允许 NULL；这些记录只读，PUT/DELETE 时返回 409 |
| 查询 GET（无 supplier_id 参数） | 返回所有 supplier_id 与 supplier_name 匹配规则命中的记录 |
| 查询 GET（传 supplier_id） | 只返回 `supplier_id` 命中的记录 |
| 查询 GET（仅传 supplier_name，fallback） | 返回 supplier_id NULL 但 supplier_name 命中的记录 |
| PUT/DELETE supplier_id NULL 记录 | **拒绝**，返回 409 Conflict；提示数据为历史只读 |
| POST 同一 URL 时 supplier_id 不同 | 视作不同记录，不冲突 |

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

**前置校验：**
- URL 记录必须存在
- `product_id` 关联的产品必须存在
- `product_id → customer → dept_id == dept_id`（部门归属通过 `crm_customer.dept_id` 间接获取，因为 `prd_customer_product` 没有 `dept_id` 字段）
- `supplier_id` 非 NULL 时，对应供应商必须存在
- 旧数据（`supplier_id IS NULL`）**不允许 DELETE**，返回 409 Conflict
- 后续接入用户权限时，由统一的 `Depends(get_current_user)` 处理细粒度权限

路由示例：
```python
@router.delete("/{url_id}", status_code=204)
def delete_url(
    url_id: int,
    db: Session = Depends(get_db),
    dept_id: str = Depends(get_current_dept_id),
):
    url = crud.get_url(db, url_id)
    if not url:
        raise HTTPException(404)
    if url.supplier_id is None:
        raise HTTPException(409, detail="历史只读数据，禁止删除")
    # 通过 crm_customer.dept_id 间接校验产品归属
    from backend.models.customer import CrmCustomer
    product = (
        db.query(PrdCustomerProduct)
        .join(CrmCustomer, CrmCustomer.id == PrdCustomerProduct.customer_id)
        .filter(
            PrdCustomerProduct.id == url.product_id,
            CrmCustomer.dept_id == dept_id,
        )
        .first()
    )
    if not product:
        raise HTTPException(404, detail="URL 不属于当前部门")
    crud.delete_url(db, url_id)
```

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
from sqlalchemy.exc import IntegrityError

# POST 时升级默认（v4 修订：补上 existing.is_default = True + 处理并发）
if existing:
    if data.is_default and not existing.is_default:
        _clear_other_defaults(db, data.product_id, data.supplier_id, exclude_id=existing.id)
        existing.is_default = True   # v4 必加
        try:
            db.commit()
        except IntegrityError:
            # 并发：另一个请求同时升级，回滚后再次查询
            db.rollback()
            return (
                db.query(PrdProductSupplierUrl).filter_by(
                    product_id=data.product_id,
                    supplier_id=data.supplier_id,
                    url=data.url,
                ).first(),
                False,
            )
        db.refresh(existing)
    return existing, False

if data.is_default:
    _clear_other_defaults(db, data.product_id, data.supplier_id)

url = PrdProductSupplierUrl(**data.model_dump())
try:
    db.add(url)
    db.commit()
except IntegrityError:
    # 并发：另一个请求已插入相同 (product_id, supplier_id, url)
    db.rollback()
    return (
        db.query(PrdProductSupplierUrl).filter_by(
            product_id=data.product_id,
            supplier_id=data.supplier_id,
            url=data.url,
        ).first(),
        False,
    )
db.refresh(url)
return url, True


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
        db.commit()
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
    - **`api.create()` payload 强制包含 supplier_id**（v4 修订必填）：
      ```typescript
      await productSupplierUrlsApi.create({
        product_id: pid,
        supplier_id: form.supplier.id,   // 必填（spec §3.3.1）
        supplier_name: form.supplier_name,
        url,
      })
      ```
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

**URL 历史写入完全由后端事务负责（路由在采购事务内一并写入 `prd_product_supplier_url`）。** 前端**不再**单独调用 `productSupplierUrlsApi.create()`，避免重复写入。

前端 `onSubmit` 只负责把每行的 `row.link` 提交到 `PurchaseCreateOnline.items[i].link`，让路由层把这些 URL 与 supplier_id 一并入库。

```typescript
// 1688 提交：每行 link 已在 items[].link 中，无需后续调用
const result = await createOnlinePurchase({
  // ...
  items: items.value.map((it) => ({
    product_id: it.product_id,
    link: it.link || null,  // 每行独立 URL
    // ...其他字段
  })),
})
```

#### 顶层 `linkUrl`（顶层供应商联系字段，v4 明确）

**该字段仅用于供应商店铺 URL，不是产品 URL。** 不删除、不改名。

| 状态 | 行为 |
|------|------|
| 提交时（1688 platform） | 写入 `PurchaseCreateOnline.shop_link` 作为供应商的店铺链接，不参与每行产品 URL |
| 提交时（wechat platform） | 留空或作为可选关联 1688 链接 |
| 不与 `row.link` 混淆 | `row.link` 是**产品 URL**（每行独立），写入 `PurchaseCreateOnline.items[i].link` |

实现要点：v4 明确顶层 `linkUrl` 与每行 `row.link` 是两个独立概念，命名上为 `supplierShopLink` 与 `itemLink`，但保持现有变量名 `linkUrl`（顶）和 `row.link`（行）；禁止把 `linkUrl` 写进 `items[i].link`。

#### 采购明细的 link 字段

`PurchaseOrderItemCreate.link` 已经存在，本次实现确保前端提交时**每行的 `row.link` 都传给 `items[i].link`**。后端在创建 `Po1688Purchase` 时使用这个 link 作为 `product_url`。

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
