# 产品-供应商-URL 关联实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 建立产品-供应商-URL 多对一关联，支持采购成功后写入历史、ProductEditDialog 和 PurchaseDialog 中的 URL 下拉选择与持久化。

**架构：** 新增 `prd_product_supplier_url` 表存储 `(product_id, supplier_id, url)` 关系；采购成功后自动写入该表；前端在供应商选择后拉取历史 URL 下拉，支持选择已有 URL 或手动输入并持久化。

**技术栈：** FastAPI (SQLAlchemy) / Vue 3 + TypeScript / Element Plus

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/models/product_supplier_url.py` | 新增 `PrdProductSupplierUrl` ORM 模型 |
| `backend/schemas/product_supplier_url.py` | Pydantic 请求/响应 schemas |
| `backend/crud/product_supplier_url.py` | CRUD 业务逻辑 |
| `backend/routers/product_supplier_url.py` | API 路由 |
| `backend/models/purchase.py` | `po_1688_purchase` 新增 `supplier_id` 字段 |
| `backend/migrations/add_product_supplier_url.py` | 数据库迁移 |
| `backend/crud/purchase.py` | 采购成功后写入 URL 历史 |
| `frontend/src/api/productSupplierUrls.ts` | 前端 API 封装 |
| `frontend/src/components/order/ProductEditDialog.vue` | 供应商链接下拉 |
| `frontend/src/components/order/PurchaseDialog.vue` | 1688 链接下拉 |

---

## 任务 1：后端模型与迁移

**文件：**
- 创建：`backend/models/product_supplier_url.py`
- 修改：`backend/models/purchase.py:72-96`
- 创建：`backend/migrations/add_product_supplier_url.py`

- [ ] **步骤 1：创建 `backend/models/product_supplier_url.py`**

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class PrdProductSupplierUrl(Base):
    __tablename__ = "prd_product_supplier_url"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    product_id    = Column(Integer, ForeignKey("prd_customer_product.id"), nullable=False, index=True)
    supplier_id   = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True, index=True)
    supplier_name = Column(String(200), nullable=False)
    url           = Column(String(500), nullable=False)
    display_name  = Column(String(100), nullable=True)
    is_default    = Column(Boolean, default=False)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **步骤 2：`po_1688_purchase` 新增 `supplier_id` 字段**

在 `backend/models/purchase.py` 的 `Po1688Purchase` 类中，在 `status` 字段前添加：

```python
supplier_id = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
```

- [ ] **步骤 3：创建迁移文件 `backend/migrations/add_product_supplier_url.py`**

```python
import sqlalchemy as sa
from database import engine, Base


def upgrade():
    with engine.begin() as conn:
        # 新表 prd_product_supplier_url
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS prd_product_supplier_url (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER,
                supplier_name VARCHAR(200) NOT NULL,
                url VARCHAR(500) NOT NULL,
                display_name VARCHAR(100),
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES prd_customer_product(id),
                FOREIGN KEY (supplier_id) REFERENCES sup_supplier(id)
            )
        """))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_product_supplier_url_product ON prd_product_supplier_url(product_id)"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_product_supplier_url_supplier ON prd_product_supplier_url(supplier_id)"))
        
        # po_1688_purchase 新增 supplier_id
        conn.execute(sa.text("ALTER TABLE po_1688_purchase ADD COLUMN supplier_id INTEGER REFERENCES sup_supplier(id)"))
        # 填充历史数据（根据 supplier_name 匹配）
        conn.execute(sa.text("""
            UPDATE po_1688_purchase
            SET supplier_id = (
                SELECT id FROM sup_supplier
                WHERE sup_supplier.supplier_name = po_1688_purchase.supplier_name
                LIMIT 1
            )
            WHERE supplier_id IS NULL
        """))


def downgrade():
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE po_1688_purchase DROP COLUMN supplier_id"))
        conn.execute(sa.text("DROP TABLE IF EXISTS prd_product_supplier_url"))
```

- [ ] **步骤 4：运行迁移**

```bash
cd d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend
python -m migrations.add_product_supplier_url
```

预期：创建 `prd_product_supplier_url` 表，`po_1688_purchase` 新增 `supplier_id` 列，历史数据按 `supplier_name` 匹配填充。

- [ ] **步骤 5：Commit**

```bash
git add backend/models/product_supplier_url.py backend/models/purchase.py backend/migrations/add_product_supplier_url.py
git commit -m "feat: add PrdProductSupplierUrl model and migration"
```

---

## 任务 2：后端 Schema 与 CRUD

**文件：**
- 创建：`backend/schemas/product_supplier_url.py`
- 创建：`backend/crud/product_supplier_url.py`

- [ ] **步骤 1：创建 `backend/schemas/product_supplier_url.py`**

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class ProductSupplierUrlCreate(BaseModel):
    product_id: int
    supplier_id: Optional[int] = None
    supplier_name: str
    url: str
    display_name: Optional[str] = None
    is_default: bool = False


class ProductSupplierUrlUpdate(BaseModel):
    url: Optional[str] = None
    display_name: Optional[str] = None
    is_default: Optional[bool] = None


class ProductSupplierUrlResponse(BaseModel):
    id: int
    product_id: int
    supplier_id: Optional[int]
    supplier_name: str
    url: str
    display_name: Optional[str]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **步骤 2：创建 `backend/crud/product_supplier_url.py`**

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.product_supplier_url import PrdProductSupplierUrl
from backend.schemas.product_supplier_url import ProductSupplierUrlCreate, ProductSupplierUrlUpdate


def list_urls(db: Session, product_id: int, supplier_name: str) -> list[PrdProductSupplierUrl]:
    return (
        db.query(PrdProductSupplierUrl)
        .filter(
            PrdProductSupplierUrl.product_id == product_id,
            PrdProductSupplierUrl.supplier_name == supplier_name,
        )
        .order_by(PrdProductSupplierUrl.is_default.desc(), PrdProductSupplierUrl.created_at.desc())
        .all()
    )


def create_url(db: Session, data: ProductSupplierUrlCreate) -> tuple[PrdProductSupplierUrl, bool]:
    """返回 (记录, 是否新建)。URL 重复时返回已有记录。"""
    existing = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == data.product_id,
        PrdProductSupplierUrl.supplier_name == data.supplier_name,
        PrdProductSupplierUrl.url == data.url,
    ).first()
    if existing:
        return existing, False

    if data.is_default:
        db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == data.product_id,
            PrdProductSupplierUrl.supplier_name == data.supplier_name,
        ).update({"is_default": False})

    url = PrdProductSupplierUrl(**data.model_dump())
    db.add(url)
    db.commit()
    db.refresh(url)
    return url, True


def update_url(db: Session, url_id: int, data: ProductSupplierUrlUpdate) -> PrdProductSupplierUrl | None:
    url = db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.id == url_id).first()
    if not url:
        return None

    if data.is_default is True:
        db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == url.product_id,
            PrdProductSupplierUrl.supplier_name == url.supplier_name,
            PrdProductSupplierUrl.id != url_id,
        ).update({"is_default": False})

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(url, field, value)

    db.commit()
    db.refresh(url)
    return url


def delete_url(db: Session, url_id: int) -> bool:
    url = db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.id == url_id).first()
    if not url:
        return False
    db.delete(url)
    db.commit()
    return True
```

- [ ] **步骤 3：Commit**

```bash
git add backend/schemas/product_supplier_url.py backend/crud/product_supplier_url.py
git commit -m "feat: add product_supplier_url schemas and CRUD"
```

---

## 任务 3：后端 API 路由

**文件：**
- 创建：`backend/routers/product_supplier_url.py`
- 修改：`backend/main.py`（注册路由）

- [ ] **步骤 1：创建 `backend/routers/product_supplier_url.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.product_supplier_url import (
    ProductSupplierUrlCreate,
    ProductSupplierUrlUpdate,
    ProductSupplierUrlResponse,
)
from backend.crud import product_supplier_url as crud


router = APIRouter(prefix="/product-supplier-urls", tags=["product-supplier-urls"])


@router.get("", response_model=list[ProductSupplierUrlResponse])
def list_urls(
    product_id: int = Query(..., description="产品 ID"),
    supplier_name: str = Query(..., description="供应商名称"),
    db: Session = Depends(get_db),
):
    return crud.list_urls(db, product_id, supplier_name)


@router.post("", response_model=ProductSupplierUrlResponse, status_code=201)
def create_url(data: ProductSupplierUrlCreate, db: Session = Depends(get_db)):
    url, created = crud.create_url(db, data)
    return url


@router.put("/{url_id}", response_model=ProductSupplierUrlResponse)
def update_url(url_id: int, data: ProductSupplierUrlUpdate, db: Session = Depends(get_db)):
    url = crud.update_url(db, url_id, data)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


@router.delete("/{url_id}", status_code=204)
def delete_url(url_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_url(db, url_id)
    if not ok:
        raise HTTPException(status_code=404, detail="URL not found")
```

- [ ] **步骤 2：在 `backend/main.py` 中注册路由**

在现有的 `include_router` 附近添加：

```python
from backend.routers.product_supplier_url import router as product_supplier_url_router
# ...
app.include_router(product_supplier_url_router)
```

（如果 `main.py` 中已有类似的 include_router 模式，遵循相同风格）

- [ ] **步骤 3：测试 API**

启动后端后，用 curl 测试：

```bash
# 列表查询（product_id=1, supplier_name="测试供应商"）
curl "http://localhost:8000/api/product-supplier-urls?product_id=1&supplier_name=测试供应商"

# 创建
curl -X POST http://localhost:8000/api/product-supplier-urls \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"supplier_name":"测试供应商","url":"https://detail.1688.com/item/1.html"}'
```

预期：返回 200/201，无报错。

- [ ] **步骤 4：Commit**

```bash
git add backend/routers/product_supplier_url.py backend/main.py
git commit -m "feat: add product_supplier_url API router"
```

---

## 任务 4：采购成功后写入 URL 历史

**文件：**
- 修改：`backend/crud/purchase.py`（在 `create_1688_purchase_batch` 函数末尾）

- [ ] **步骤 1：在 `create_1688_purchase_batch` 中追加 URL 历史写入逻辑**

在 `create_1688_purchase_batch()` 函数的 `db.commit()` 之后、`return created_records` 之前插入：

```python
# 写入 URL 历史到 prd_product_supplier_url
from backend.models.product_supplier_url import PrdProductSupplierUrl
for p in created_records:
    if not p.product_url:
        continue
    existing = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == p.product_id,
        PrdProductSupplierUrl.url == p.product_url,
    ).first()
    if not existing:
        db.add(PrdProductSupplierUrl(
            product_id=p.product_id,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier_name,
            url=p.product_url,
            is_default=False,
        ))
        db.commit()
```

**注意：** 需要在文件顶部添加 import：
```python
from backend.models.product_supplier_url import PrdProductSupplierUrl
```

- [ ] **步骤 2：Commit**

```bash
git add backend/crud/purchase.py
git commit -m "feat: write product URL to history after 1688 purchase"
```

---

## 任务 5：前端 API 封装

**文件：**
- 创建：`frontend/src/api/productSupplierUrls.ts`

- [ ] **步骤 1：创建 `frontend/src/api/productSupplierUrls.ts`**

```typescript
import client from './client'

export interface ProductSupplierUrl {
  id: number
  product_id: number
  supplier_id: number | null
  supplier_name: string
  url: string
  display_name: string | null
  is_default: boolean
  created_at: string
}

export interface ProductSupplierUrlCreate {
  product_id: number
  supplier_id?: number | null
  supplier_name: string
  url: string
  display_name?: string | null
  is_default?: boolean
}

export interface ProductSupplierUrlUpdate {
  url?: string
  display_name?: string | null
  is_default?: boolean
}

const BASE = '/api/product-supplier-urls'

export const productSupplierUrlsApi = {
  list(productId: number, supplierName: string): Promise<ProductSupplierUrl[]> {
    return client.get(`${BASE}?product_id=${productId}&supplier_name=${encodeURIComponent(supplierName)}`)
  },
  create(data: ProductSupplierUrlCreate): Promise<ProductSupplierUrl> {
    return client.post(BASE, data)
  },
  update(id: number, data: ProductSupplierUrlUpdate): Promise<ProductSupplierUrl> {
    return client.put(`${BASE}/${id}`, data)
  },
  remove(id: number): Promise<void> {
    return client.delete(`${BASE}/${id}`)
  },
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/api/productSupplierUrls.ts
git commit -m "feat: add productSupplierUrls API client"
```

---

## 任务 6：ProductEditDialog 供应商链接下拉

**文件：**
- 修改：`frontend/src/components/order/ProductEditDialog.vue:357-364`

- [ ] **步骤 1：改造 `ProductEditDialog` 的供应商链接字段**

将现有的 `<FieldInput v-model="form.shop_url">` 改造为下拉选择 + 手动输入：

```vue
<div class="purchase-cost-cell link-cell">
  <el-select
    v-model="form.shop_url"
    filterable
    allow-create
    default-first-option
    placeholder="选择或输入1688链接"
    :disabled="formLocked"
    @change="onShopUrlChange"
    style="width: 100%"
  >
    <el-option
      v-for="u in supplierUrlOptions"
      :key="u.id || u.url"
      :label="u.display_name || u.url"
      :value="u.url"
    />
  </el-select>
</div>
```

- [ ] **步骤 2：添加相关状态和方法**

在 script 中添加：

```typescript
import { productSupplierUrlsApi } from '@/api/productSupplierUrls'

const supplierUrlOptions = ref<ProductSupplierUrl[]>([])

async function loadSupplierUrls() {
  if (!form.supplier_name) {
    supplierUrlOptions.value = []
    return
  }
  try {
    // product_id 从 item.value 获取（编辑已有产品时）
    const pid = item.value?.product_id
    if (!pid) {
      supplierUrlOptions.value = []
      return
    }
    const res = await productSupplierUrlsApi.list(pid, form.supplier_name)
    supplierUrlOptions.value = res.data || []
  } catch (e) {
    supplierUrlOptions.value = []
  }
}

async function onShopUrlChange(url: string) {
  // 持久化到 prd_product_supplier_url
  try {
    const pid = item.value?.product_id
    if (pid && form.supplier_name && url) {
      await productSupplierUrlsApi.create({
        product_id: pid,
        supplier_name: form.supplier_name,
        url,
      })
      // 刷新下拉列表
      await loadSupplierUrls()
    }
  } catch (e) {
    console.warn('[ProductEditDialog] 保存采购链接失败', e)
  }
  // 同时写入 pi_item.shop_url
  saveField('shop_url', url)
}
```

- [ ] **步骤 3：在 `onSupplierSelect` 和 `onSupplierClear` 中调用 `loadSupplierUrls`**

在 `onSupplierSelect` 函数末尾添加：
```typescript
loadSupplierUrls()
```

在 `onSupplierClear` 函数中添加：
```typescript
supplierUrlOptions.value = []
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/components/order/ProductEditDialog.vue
git commit -m "feat: add supplier URL dropdown to ProductEditDialog"
```

---

## 任务 7：PurchaseDialog 1688 链接下拉

**文件：**
- 修改：`frontend/src/components/order/PurchaseDialog.vue:67-69`

- [ ] **步骤 1：改造 `PurchaseDialog` 的 1688 链接字段**

将现有的 `<el-input v-model="linkUrl">` 改造为下拉选择 + 手动输入：

```vue
<el-form-item label="1688链接">
  <el-select
    v-model="linkUrl"
    filterable
    allow-create
    default-first-option
    placeholder="选择或输入1688产品链接"
    style="width: 100%"
  >
    <el-option
      v-for="u in currentItemUrls"
      :key="u.id || u.url"
      :label="u.display_name || u.url"
      :value="u.url"
    />
  </el-select>
</el-form-item>
```

- [ ] **步骤 2：添加相关状态和方法**

在 script 中添加：

```typescript
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'

// 当前选中供应商对应的 URL 列表（按当前 tab 第一个产品获取 product_id）
const currentItemUrls = ref<ProductSupplierUrl[]>([])

async function loadCurrentItemUrls() {
  if (!pendingSupplierState.supplier) return
  const pid = items.value[0]?.product_id
  if (!pid) return
  try {
    const res = await productSupplierUrlsApi.list(pid, pendingSupplierState.supplier.supplier_name)
    currentItemUrls.value = res.data || []
  } catch (e) {
    currentItemUrls.value = []
  }
}
```

- [ ] **步骤 3：在 pending 回填逻辑中调用 `loadCurrentItemUrls`**

在 `open()` 函数的 pending 逻辑中，1688 平台时添加：
```typescript
if (supplierPlatform === '1688') {
  const name = pending.supplier!.supplier_name || ''
  shopName.value = name
  autoFillShopName.value = name
  if (pending.shop_link) {
    linkUrl.value = pending.shop_link
  }
  if (pending.wechat_id) {
    contactWechat.value = pending.wechat_id
  }
  // 加载该产品的历史 URL 下拉
  await loadCurrentItemUrls()
}
```

- [ ] **步骤 4：提交成功后写入 URL 历史**

在 `onSubmit()` 中 1688 采购分支的 `createOnlinePurchase` 成功后添加：

```typescript
if (platform.value === '1688' && linkUrl.value) {
  const pid = items.value[0]?.product_id
  if (pid && pendingSupplierState.supplier) {
    productSupplierUrlsApi.create({
      product_id: pid,
      supplier_id: pendingSupplierState.supplier.id,
      supplier_name: pendingSupplierState.supplier.supplier_name,
      url: linkUrl.value,
    }).catch(e => console.warn('[PurchaseDialog] 写入采购链接历史失败', e))
  }
}
```

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/components/order/PurchaseDialog.vue
git commit -m "feat: add 1688 URL dropdown to PurchaseDialog"
```

---

## 规格覆盖度自检

| 规格章节 | 对应任务 |
|---------|---------|
| 新增表 `prd_product_supplier_url` | 任务 1 |
| `po_1688_purchase` 新增 `supplier_id` | 任务 1 |
| 迁移脚本 | 任务 1 |
| API 端点 CRUD | 任务 2 + 任务 3 |
| 采购成功后写入 URL 历史 | 任务 4 |
| 前端 API 封装 | 任务 5 |
| `ProductEditDialog` URL 下拉 | 任务 6 |
| `PurchaseDialog` URL 下拉 + 提交写入 | 任务 7 |

所有规格章节均有对应任务，无遗漏。
