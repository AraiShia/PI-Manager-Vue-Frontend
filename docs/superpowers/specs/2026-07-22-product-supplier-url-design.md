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

    id              = Column(Integer, primary_key=True)
    product_id      = Column(Integer, ForeignKey("prd_customer_product.id"), nullable=False)
    supplier_id     = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
    supplier_name   = Column(String(200), nullable=False)   # 快照，用于无 supplier_id 时查询
    url             = Column(String(500), nullable=False)
    display_name    = Column(String(100), nullable=True)    # 可选显示名，如"链接A"
    is_default      = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.2 `po_1688_purchase` 新增字段

```python
supplier_id = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
```

用于建立历史采购记录与供应商的关联，支持按供应商聚合 URL。

### 2.3 索引

```sql
CREATE INDEX ix_product_supplier_url_product ON prd_product_supplier_url(product_id);
CREATE INDEX ix_product_supplier_url_supplier ON prd_product_supplier_url(supplier_id);
CREATE UNIQUE INDEX ux_product_supplier_url_unique ON prd_product_supplier_url(product_id, supplier_id, url);
```

---

## 3. API 设计

### 3.1 路由 `/api/product-supplier-urls`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/product-supplier-urls` | GET | 查询列表（按 `product_id` + `supplier_name` 过滤） |
| `/api/product-supplier-urls` | POST | 创建 URL 记录 |
| `/api/product-supplier-urls/{id}` | PUT | 更新 URL 记录 |
| `/api/product-supplier-urls/{id}` | DELETE | 删除 URL 记录 |

### 3.2 GET 查询参数

```
GET /api/product-supplier-urls?product_id=123&supplier_name=xxx
```

返回按 `is_default DESC, created_at DESC` 排序的列表。

### 3.3 POST 请求体

```json
{
  "product_id": 123,
  "supplier_id": 456,
  "supplier_name": "供应商A",
  "url": "https://detail.1688.com/item/123.html",
  "display_name": "店铺A-链接1",
  "is_default": true
}
```

**逻辑：**
- URL 重复时返回已有记录，不重复创建
- 设置 `is_default=true` 时，自动取消同产品同供应商的其他默认

### 3.4 PUT 请求体

```json
{
  "url": "https://detail.1688.com/item/456.html",
  "display_name": "新链接",
  "is_default": true
}
```

---

## 4. 采购成功后的 URL 写入逻辑

在 `create_1688_purchase_batch()` 中，采购明细写入后，追加写入 `prd_product_supplier_url`：

```python
# 采购成功后写入 URL 历史
for p in created_records:
    existing = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == p.product_id,
        PrdProductSupplierUrl.url == p.product_url
    ).first()
    if not existing and p.product_url:
        db.add(PrdProductSupplierUrl(
            product_id=p.product_id,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier_name,
            url=p.product_url,
            is_default=False,
        ))
```

---

## 5. 前端改动

### 5.1 API 层

新增 `src/api/productSupplierUrls.ts`：
- `list(productId, supplierName)` — 查询 URL 列表
- `create(payload)` — 创建 URL
- `update(id, payload)` — 更新 URL
- `remove(id)` — 删除 URL

### 5.2 `ProductEditDialog` 改动

**供应商链接字段（第 357-364 行）：**

- `SupplierSearchSelect` 选择供应商后：
  - 查询 `prd_product_supplier_url`（按 `product_id + supplier_name`）
  - 将 URL 列表作为下拉展示
  - 用户可选择已有 URL 或手动输入新 URL
  - 选/填后调用 `api.create()` 或 `api.update()` 持久化
  - 同时 `saveField('shop_url', form.shop_url)` 写入 `pi_item.shop_url`

### 5.3 `PurchaseDialog` 改动

**1688 链接字段（第 67-69 行）：**

- 选择供应商后：
  - 查询 `prd_product_supplier_url`（按 `product_id + supplier_name`）
  - 将 URL 列表作为下拉展示（`el-select` + `allow-create`）
  - 用户可选择已有 URL 或手动输入
  - 提交成功后写入 `prd_product_supplier_url`

---

## 6. 批量导入时的自动回填（后续实现）

当前 scope 仅覆盖：
1. `ProductEditDialog` 选择供应商后的 URL 下拉
2. `PurchaseDialog` 的 URL 下拉和提交写入

批量导入时的自动回填（方案 A 中的 `getRecent1688Urls` 按供应商过滤）留作后续任务。

---

## 7. 范围

| 功能 | 范围 |
|------|------|
| 新增表 + 迁移 | ✅ 本次 |
| CRUD API | ✅ 本次 |
| 采购成功后写入 URL 历史 | ✅ 本次 |
| `ProductEditDialog` URL 下拉 | ✅ 本次 |
| `PurchaseDialog` URL 下拉 + 提交写入 | ✅ 本次 |
| 批量导入自动回填 | ❌ 后续 |
