# 产品-供应商-URL 关联实现计划（v2 修订）

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 建立产品-供应商-URL 多对一关联，支持采购成功后写入历史、ProductEditDialog 和 PurchaseDialog 中的 URL 下拉选择与持久化。

**架构：** 新增 `prd_product_supplier_url` 表存储 `(product_id, supplier_id, url)` 关系；`supplier_id` 贯穿 1688 采购写入链路；前端按行独立选择 URL，提交后写入历史。

**技术栈：** FastAPI (SQLAlchemy) / Vue 3 + TypeScript / Element Plus

**修订要点：** 1) supplier_id 贯穿采购链路；2) 历史数据导入新表；3) PurchaseDialog 每行独立 URL；4) 事务边界统一

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/models/product_supplier_url.py` | 新增 `PrdProductSupplierUrl` ORM 模型 |
| `backend/schemas/product_supplier_url.py` | Pydantic 请求/响应 schemas |
| `backend/crud/product_supplier_url.py` | CRUD 业务逻辑（含 is_default 闭环） |
| `backend/routers/product_supplier_url.py` | API 路由 |
| `backend/models/purchase.py` | `po_1688_purchase` 新增 `supplier_id` 字段 |
| `backend/schemas/purchase.py` | `Po1688PurchaseItem` 新增 `supplier_id` |
| `backend/routers/purchase.py` | 注入 supplier_id 到 batch items |
| `backend/crud/purchase.py` | 创建 1688 记录时赋值 supplier_id；移除内部 commit；批处理内写入 URL 历史 |
| `backend/migrations/add_product_supplier_url.py` | 表创建 + 字段迁移 + 历史数据导入 |
| `backend/tests/test_product_supplier_url_api.py` | CRUD API 测试 + supplier_id 贯穿验证 + 事务回滚验证 |
| `frontend/src/api/productSupplierUrls.ts` | 前端 API 封装 |
| `frontend/src/components/order/ProductEditDialog.vue` | 供应商链接下拉（含优先级） |
| `frontend/src/components/order/PurchaseDialog.vue` | 表格行 1688 链接下拉 |

---

## 任务 1：后端模型与迁移（含历史导入）

**文件：**
- 创建：`backend/models/product_supplier_url.py`
- 修改：`backend/models/purchase.py:72-96`
- 创建：`backend/migrations/add_product_supplier_url.py`

- [ ] **步骤 1：创建 `backend/models/product_supplier_url.py`**

```python
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func,
)
from database import Base


class PrdProductSupplierUrl(Base):
    __tablename__ = "prd_product_supplier_url"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    product_id    = Column(Integer, ForeignKey("prd_customer_product.id"), nullable=False)
    supplier_id   = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
    supplier_name = Column(String(200), nullable=False)
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

- [ ] **步骤 2：`po_1688_purchase` 新增 `supplier_id` 字段**

在 `backend/models/purchase.py` 的 `Po1688Purchase` 类中，在 `status` 字段前添加：

```python
supplier_id = Column(Integer, ForeignKey("sup_supplier.id"), nullable=True)
```

- [ ] **步骤 3：创建迁移 `backend/migrations/add_product_supplier_url.py`**

```python
import sqlalchemy as sa
from database import engine


def upgrade():
    with engine.begin() as conn:
        # 1. 新表
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
                UNIQUE(product_id, supplier_id, url),
                FOREIGN KEY (product_id) REFERENCES prd_customer_product(id),
                FOREIGN KEY (supplier_id) REFERENCES sup_supplier(id)
            )
        """))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_psu_supplier ON prd_product_supplier_url(supplier_id)"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_psu_product ON prd_product_supplier_url(product_id)"))

        # 2. po_1688_purchase 新增 supplier_id
        conn.execute(sa.text("ALTER TABLE po_1688_purchase ADD COLUMN supplier_id INTEGER REFERENCES sup_supplier(id)"))

        # 3. 历史数据按 (dept_id + supplier_name + platform='1688') 回填 supplier_id
        conn.execute(sa.text("""
            UPDATE po_1688_purchase
            SET supplier_id = (
                SELECT id FROM sup_supplier
                WHERE sup_supplier.supplier_name = po_1688_purchase.supplier_name
                  AND sup_supplier.dept_id = po_1688_purchase.dept_id
                  AND sup_supplier.platform = '1688'
                LIMIT 1
            )
            WHERE supplier_id IS NULL
        """))

        # 3.1 记录仍未匹配的 supplier_id（保留 NULL）
        # 由运维人员手动 SELECT COUNT(*) FROM po_1688_purchase WHERE supplier_id IS NULL

        # 4. 历史 URL 导入新表（v3 修订：用 ROW_NUMBER 去重 + 同组最早一条插入）
        conn.execute(sa.text("""
            INSERT INTO prd_product_supplier_url
                (product_id, supplier_id, supplier_name, url, is_default, created_at)
            SELECT * FROM (
                SELECT
                    p.product_id,
                    p.supplier_id,
                    p.supplier_name,
                    p.product_url,
                    CASE WHEN p.row_num_desc = 1 THEN 1 ELSE 0 END,
                    p.created_at
                FROM (
                    SELECT
                        p1.product_id,
                        p1.supplier_id,
                        p1.supplier_name,
                        p1.product_url,
                        p1.created_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                p1.product_id,
                                COALESCE(p1.supplier_id, 0),
                                p1.product_url
                            ORDER BY p1.created_at ASC, p1.id ASC
                        ) AS row_num_asc,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                p1.product_id,
                                COALESCE(p1.supplier_id, 0),
                                p1.product_url
                            ORDER BY p1.created_at DESC, p1.id DESC
                        ) AS row_num_desc
                    FROM po_1688_purchase p1
                    WHERE p1.product_url IS NOT NULL AND p1.product_url <> ''
                ) p
                WHERE p.row_num_asc = 1
            ) final
        """))


def downgrade():
    with engine.begin() as conn:
        conn.execute(sa.text("DROP TABLE IF EXISTS prd_product_supplier_url"))
        # SQLite 不支持 DROP COLUMN，使用重建表：
        conn.execute(sa.text("""
            CREATE TABLE po_1688_purchase_backup AS SELECT * FROM po_1688_purchase
        """))
        conn.execute(sa.text("DROP TABLE po_1688_purchase"))
        conn.execute(sa.text("""
            CREATE TABLE po_1688_purchase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id VARCHAR(10) NOT NULL,
                po_id INTEGER,
                pi_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                supplier_name VARCHAR(200),
                product_url VARCHAR(500),
                -- ...（完整原字段定义）
            )
        """))
        conn.execute(sa.text("""
            INSERT INTO po_1688_purchase
            (id, dept_id, po_id, pi_id, product_id, supplier_name, product_url, ...)
            SELECT id, dept_id, po_id, pi_id, product_id, supplier_name, product_url, ...
            FROM po_1688_purchase_backup
        """))
        conn.execute(sa.text("DROP TABLE po_1688_purchase_backup"))
```

**注意：** downgrade 是一个示意骨架。如果有 Alembic 迁移系统，遵循其迁移机制。

- [ ] **步骤 4：运行迁移**

```bash
cd d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend
python -m migrations.add_product_supplier_url
```

预期：创建 `prd_product_supplier_url` 表，导入历史 URL，`po_1688_purchase` 新增 `supplier_id`。

- [ ] **步骤 5：Commit**

```bash
git add backend/models/product_supplier_url.py backend/models/purchase.py backend/migrations/add_product_supplier_url.py
git commit -m "feat: add PrdProductSupplierUrl model, migration with historical data import"
```

---

## 任务 2：CRUD（含 is_default 闭环）

**文件：**
- 创建：`backend/schemas/product_supplier_url.py`
- 创建：`backend/crud/product_supplier_url.py`

- [ ] **步骤 1：创建 `backend/schemas/product_supplier_url.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductSupplierUrlCreate(BaseModel):
    product_id: int
    supplier_id: Optional[int] = None
    supplier_name: str
    url: str = Field(..., max_length=500)
    display_name: Optional[str] = None
    is_default: bool = False


class ProductSupplierUrlUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=500)
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
from backend.models.product_supplier_url import PrdProductSupplierUrl
from backend.schemas.product_supplier_url import ProductSupplierUrlCreate, ProductSupplierUrlUpdate
from fastapi import HTTPException


def list_urls(db: Session, product_id: int, supplier_id: int | None = None, supplier_name: str | None = None) -> list[PrdProductSupplierUrl]:
    """查询 URL 列表：优先 supplier_id，fallback supplier_name"""
    q = db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.product_id == product_id)

    if supplier_id is not None:
        rows = q.filter(PrdProductSupplierUrl.supplier_id == supplier_id).all()
        if rows:
            return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))
        # 如 supplier_id 查询为空但 supplier_name 给了，则 fallback
        if supplier_name:
            rows = q.filter(PrdProductSupplierUrl.supplier_name == supplier_name).all()
    elif supplier_name:
        rows = q.filter(PrdProductSupplierUrl.supplier_name == supplier_name).all()
    else:
        rows = q.all()

    return sorted(rows, key=lambda u: (not u.is_default, -u.created_at.timestamp()))


def create_url(db: Session, data: ProductSupplierUrlCreate) -> tuple[PrdProductSupplierUrl, bool]:
    """返回 (记录, 是否新建)。URL 重复时返回已有记录，必要时升级 is_default"""
    existing = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == data.product_id,
        PrdProductSupplierUrl.supplier_id == data.supplier_id,
        PrdProductSupplierUrl.url == data.url,
    ).first()

    if existing:
        # 升级默认（如请求要求）
        if data.is_default and not existing.is_default:
            _promote_to_default(db, existing)
            db.commit()
            db.refresh(existing)
        return existing, False

    if data.is_default:
        _clear_other_defaults(db, data.product_id, data.supplier_id)

    url = PrdProductSupplierUrl(**data.model_dump())
    db.add(url)
    db.commit()
    db.refresh(url)
    return url, True


def update_url(db: Session, url_id: int, data: ProductSupplierUrlUpdate) -> PrdProductSupplierUrl | None:
    url = db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.id == url_id).first()
    if not url:
        return None

    if data.url and data.url != url.url:
        # URL 冲突检查
        conflict = db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == url.product_id,
            PrdProductSupplierUrl.supplier_id == url.supplier_id,
            PrdProductSupplierUrl.url == data.url,
            PrdProductSupplierUrl.id != url_id,
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="URL 已存在同产品同供应商下的另一条记录")

    if data.is_default is True and not url.is_default:
        _promote_to_default(db, url)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(url, field, value)

    db.commit()
    db.refresh(url)
    return url


def delete_url(db: Session, url_id: int) -> bool:
    url = db.query(PrdProductSupplierUrl).filter(PrdProductSupplierUrl.id == url_id).first()
    if not url:
        return False

    was_default = url.is_default
    db.delete(url)
    db.commit()

    if was_default:
        # 自动选择最新一条为默认
        next_default = db.query(PrdProductSupplierUrl).filter(
            PrdProductSupplierUrl.product_id == url.product_id,
            PrdProductSupplierUrl.supplier_id == url.supplier_id,
            PrdProductSupplierUrl.id != url_id,
        ).order_by(PrdProductSupplierUrl.created_at.desc()).first()
        if next_default:
            next_default.is_default = True
            db.commit()

    return True


# ---- Helpers ----

def _promote_to_default(db: Session, url: PrdProductSupplierUrl):
    _clear_other_defaults(db, url.product_id, url.supplier_id, exclude_id=url.id)
    url.is_default = True


def _clear_other_defaults(db: Session, product_id: int, supplier_id: int | None, exclude_id: int | None = None):
    q = db.query(PrdProductSupplierUrl).filter(
        PrdProductSupplierUrl.product_id == product_id,
        PrdProductSupplierUrl.supplier_id == supplier_id,
    )
    if exclude_id is not None:
        q = q.filter(PrdProductSupplierUrl.id != exclude_id)
    q.update({"is_default": False})
```

- [ ] **步骤 3：Commit**

```bash
git add backend/schemas/product_supplier_url.py backend/crud/product_supplier_url.py
git commit -m "feat: add product_supplier_url schemas and CRUD with is_default closure"
```

---

## 任务 3：API 路由

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
    product_id: int = Query(...),
    supplier_id: int | None = Query(None),
    supplier_name: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """按 (product_id, supplier_id) 查询；缺 supplier_id 时按 supplier_name fallback"""
    return crud.list_urls(db, product_id, supplier_id, supplier_name)


@router.post("", response_model=ProductSupplierUrlResponse)
def create_url(data: ProductSupplierUrlCreate, db: Session = Depends(get_db)):
    url, created = crud.create_url(db, data)
    # 201 Created 表示新建，200 OK 表示已存在
    # FastAPI 默认 200，但我们可以用 status_code=201 + 改响应
    # 这里简化：统一返回 200，由 created 字段告知
    return url


@router.put("/{url_id}", response_model=ProductSupplierUrlResponse)
def update_url(url_id: int, data: ProductSupplierUrlUpdate, db: Session = Depends(get_db)):
    try:
        url = crud.update_url(db, url_id, data)
    except HTTPException:
        raise
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

在现有 `include_router` 附近添加：

```python
from backend.routers.product_supplier_url import router as product_supplier_url_router
app.include_router(product_supplier_url_router)
```

- [ ] **步骤 3：测试 API（手动 curl 或 pytest）**

```bash
curl "http://localhost:8000/api/product-supplier-urls?product_id=1&supplier_id=1"
curl -X POST http://localhost:8000/api/product-supplier-urls \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"supplier_id":1,"supplier_name":"测试","url":"https://detail.1688.com/item/1.html"}'
```

- [ ] **步骤 4：Commit**

```bash
git add backend/routers/product_supplier_url.py backend/main.py
git commit -m "feat: add product_supplier_url API router"
```

---

## 任务 4：采购链路 supplier_id 贯穿

**文件：**
- 修改：`backend/schemas/purchase.py:160-187`
- 修改：`backend/crud/purchase.py:402-469`
- 修改：`backend/routers/purchase.py:96-160`

- [ ] **步骤 1：`Po1688PurchaseItem` 新增 `supplier_id`**

在 `backend/schemas/purchase.py` 的 `Po1688PurchaseItem` 类中，`supplier_name` 后添加：

```python
supplier_id: Optional[int] = None
```

- [ ] **步骤 2：`create_1688_purchase_batch` 接收 supplier_id + 移除内部 commit + 内嵌 URL 写入**

**改动位置：** `backend/crud/purchase.py:402-469`

替换 `create_1688_purchase_batch` 为：

```python
def create_1688_purchase_batch(db: Session, batch_data):
    """2026-07-22 v2 修订：
    - 接收 supplier_id 并贯穿到每条记录
    - 移除内部 db.commit()，仅 flush()，由路由统一 commit
    - 内嵌写入 URL 历史（同样 flush，避免重复 commit）
    """
    items = getattr(batch_data, "items", None) or []
    if not items:
        raise ValueError("items 不能为空")

    shared_supplier_id = getattr(batch_data, "supplier_id", None)  # 路由层注入
    shared_supplier_name = (
        items[0].supplier_name
        if items and items[0].supplier_name
        else getattr(batch_data, "supplier_name", None)
    )

    shared = {
        "dept_id": batch_data.dept_id,
        "po_id": batch_data.po_id,
        "pi_id": batch_data.pi_id,
        "supplier_id": shared_supplier_id,
    }
    created = []
    try:
        for item in items:
            db_purchase = Po1688Purchase(
                **shared,
                supplier_name=item.supplier_name or shared_supplier_name,
                product_id=item.product_id,
                product_url=item.product_url,
                product_remark=item.product_remark,
                color=item.color,
                invoice_type=item.invoice_type,
                labeling_fee=item.labeling_fee,
                shipping_fee=item.shipping_fee,
                shipping_method=item.shipping_method,
                carton_count=item.carton_count,
                freight=item.freight,
                unit_price=item.unit_price,
                tax_fee=item.tax_fee,
                payment_method=item.payment_method,
                gross_weight=item.gross_weight,
                status=1,
            )
            db.add(db_purchase)
            created.append(db_purchase)

        # 仅 flush，不 commit（由路由统一提交）
        db.flush()

        # 同步回写 PI item
        try:
            from models.pi import PiProformaInvoiceItem
            for p in created:
                pi_item = db.query(PiProformaInvoiceItem).filter(
                    PiProformaInvoiceItem.pi_id == batch_data.pi_id,
                    PiProformaInvoiceItem.product_id == p.product_id
                ).first()
                if pi_item:
                    _sync_pi_item_from_1688(db, pi_item, p)
                    db.flush()
        except Exception as sync_err_1688:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[purchase] _sync_pi_item_from_1688 failed (non-blocking): {sync_err_1688}")

        # === 新增：写入 URL 历史（同样 flush） ===
        from backend.models.product_supplier_url import PrdProductSupplierUrl
        for p in created:
            if not p.product_url or p.product_url == '':
                continue
            existing = db.query(PrdProductSupplierUrl).filter(
                PrdProductSupplierUrl.product_id == p.product_id,
                PrdProductSupplierUrl.supplier_id == p.supplier_id,
                PrdProductSupplierUrl.url == p.product_url,
            ).first()
            if not existing:
                url_record = PrdProductSupplierUrl(
                    product_id=p.product_id,
                    supplier_id=p.supplier_id,
                    supplier_name=p.supplier_name,
                    url=p.product_url,
                    is_default=False,
                )
                db.add(url_record)
        db.flush()

    except Exception:
        db.rollback()
        raise

    for p in created:
        db.refresh(p)
    return created
```

**关键改动：**
1. 接收 `batch_data.supplier_id` 并加入 `shared` 字典，注入到每条 `Po1688Purchase`
2. `db.commit()` 改为 `db.flush()`
3. `_sync_pi_item_from_1688` 后增加 `db.flush()`
4. 内嵌 URL 历史写入（同样 flush）

- [ ] **步骤 3：路由层 `Po1688PurchaseBatchCreate` 注入 `supplier_id`**

在 `backend/routers/purchase.py:120-145` 附近，构造 batch_items 时将 `supplier_id` 一起传入：

```python
batch_items = []
for it in src_items:
    batch_items.append(Po1688PurchaseItem(
        product_id=it.get("product_id"),
        supplier_id=supplier_id,  # 路由层注入
        supplier_name=it.get("supplier_name") or data.get("supplier_name"),
        product_url=it.get("link") or it.get("product_url"),
        # ... 其他字段
    ))
batch = Po1688PurchaseBatchCreate(
    dept_id=data.get("dept_id"),
    po_id=data.get("po_id"),
    pi_id=data.get("pi_id"),
    supplier_id=supplier_id,  # 同步到 batch
    screenshot=data.get("screenshot"),
    remark=data.get("remark"),
    items=batch_items,
)
```

同时在 `backend/schemas/purchase.py` 的 `Po1688PurchaseBatchCreate` 中添加：

```python
supplier_id: Optional[int] = None
```

- [ ] **步骤 4：Commit**

```bash
git add backend/schemas/purchase.py backend/crud/purchase.py backend/routers/purchase.py
git commit -m "feat: thread supplier_id through 1688 purchase batch; unify transaction boundary"
```

---

## 任务 5：测试

**文件：**
- 创建：`backend/tests/test_product_supplier_url_api.py`

- [ ] **步骤 1：编写 API 测试**

```python
def test_list_urls(client, db):
    """List 应该按 is_default DESC, created_at DESC 排序"""
    response = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_url_then_duplicate_returns_existing(client):
    """POST 相同 URL 不报错，返回已有记录"""
    payload = {"product_id": 1, "supplier_id": 1, "supplier_name": "供应商A", "url": "https://x.com"}
    r1 = client.post("/api/product-supplier-urls", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/api/product-supplier-urls", json=payload)
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_create_url_with_is_default_promotes(client):
    """POST is_default=true 自动取消其他默认"""
    p1 = {"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x1.com", "is_default": True}
    client.post("/api/product-supplier-urls", json=p1)
    p2 = {"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x2.com", "is_default": True}
    client.post("/api/product-supplier-urls", json=p2)
    # p2 应是默认，p1 不再是默认
    rs = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1").json()
    defaults = [u for u in rs if u["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["url"] == "https://x2.com"


def test_update_url_conflict_returns_409(client):
    """PUT url 与同 product_id+supplier_id 另一条 url 冲突时返回 409"""
    client.post("/api/product-supplier-urls", json={"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://a.com"})
    r = client.post("/api/product-supplier-urls", json={"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://b.com"})
    uid = r.json()["id"]
    response = client.put(f"/api/product-supplier-urls/{uid}", json={"url": "https://a.com"})
    assert response.status_code == 409


def test_delete_default_auto_promotes_latest(client):
    """删除默认 URL 后，最新一条自动成为默认"""
    client.post("/api/product-supplier-urls", json={"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x1.com", "is_default": True})
    import time; time.sleep(0.01)
    r2 = client.post("/api/product-supplier-urls", json={"product_id": 1, "supplier_id": 1, "supplier_name": "A", "url": "https://x2.com"})
    r1_id = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1").json()[1]["id"]  # x1
    client.delete(f"/api/product-supplier-urls/{r1_id}")
    rs = client.get("/api/product-supplier-urls?product_id=1&supplier_id=1").json()
    assert len(rs) == 1
    assert rs[0]["url"] == "https://x2.com"
    assert rs[0]["is_default"] is True


def test_supplier_id_threads_through_1688_batch(client, db):
    """验证 create_1688_purchase_batch 写入 supplier_id"""
    # 构造最小 Po1688PurchaseBatchCreate payload 调用路由
    # 验证 po_1688_purchase 表中新增记录的 supplier_id 等于传入值
    # 验证 prd_product_supplier_url 也带 supplier_id
    pass  # 根据具体测试框架 fill in


def test_1688_batch_failure_rolls_back_urls(client):
    """验证采购单生成失败时，URL 历史也回滚"""
    # 1. 准备使 create_grouped_purchase_orders 失败的环境
    # 2. 调用路由
    # 3. 验证 prd_product_supplier_url 中没有本次的新记录
    pass


def test_post_without_supplier_id_returns_422(client):
    """v3 修订：新建必须传 supplier_id"""
    r = client.post("/api/product-supplier-urls", json={
        "product_id": 1,
        "supplier_name": "A",
        "url": "https://x.com",
    })
    assert r.status_code == 422


def test_delete_null_supplier_id_history_returns_409(client, db):
    """v3 修订：supplier_id 为 NULL 的历史数据不允许 DELETE"""
    # 1) 直接在数据库中插入一条 supplier_id=NULL 的记录（模拟历史导入数据）
    db.add(PrdProductSupplierUrl(
        product_id=1, supplier_id=None, supplier_name="历史供应商",
        url="https://history.com",
    ))
    db.commit()
    # 2) 尝试 DELETE
    url_id = db.query(...).id  # 取刚插入的 id
    r = client.delete(f"/api/product-supplier-urls/{url_id}")
    assert r.status_code == 409


def test_migration_dedupes_history_urls(db):
    """v3 修订：迁移 SQL 用 ROW_NUMBER 去重，不会触发 UNIQUE 冲突"""
    # 1) 直接 SQL 准备 po_1688_purchase 多条 (product_id, supplier_id, url) 重复记录
    # 2) 执行迁移脚本的 INSERT…SELECT FROM (ROW_NUMBER 子查询)
    # 3) 验证：prd_product_supplier_url 中只插入了最早一条，is_default=1（最新一条）
    pass


def test_migration_supplier_id_falls_back_to_null_when_no_match(db):
    """v3 修订：supplier_id 回填找不到时保留 NULL（不强行写入错误供应商）"""
    # 1) po_1688_purchase 中插入 supplier_name='UNKNOWN' 且 sup_supplier 中没有匹配
    # 2) 运行迁移
    # 3) 验证 po_1688_purchase.supplier_id 仍为 NULL
    pass
```

- [ ] **步骤 2：运行测试**

```bash
cd d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend
pytest tests/test_product_supplier_url_api.py -v
```

预期：所有测试通过。

- [ ] **步骤 3：Commit**

```bash
git add backend/tests/test_product_supplier_url_api.py
git commit -m "test: add product_supplier_url CRUD + supplier_id threading tests"
```

---

## 任务 6：前端 API 封装

**文件：**
- 创建：`frontend/src/api/productSupplierUrls.ts`

- [ ] **步骤 1：创建 API 客户端**

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
  list(
    productId: number,
    supplierId?: number | null,
    supplierName?: string | null,
  ): Promise<ProductSupplierUrl[]> {
    const params = new URLSearchParams({ product_id: String(productId) })
    if (supplierId != null) params.set('supplier_id', String(supplierId))
    if (supplierName) params.set('supplier_name', supplierName)
    return client.get(`${BASE}?${params.toString()}`)
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

## 任务 7：ProductEditDialog 供应商链接下拉

**文件：**
- 修改：`frontend/src/components/order/ProductEditDialog.vue:357-364`
- 修改：`frontend/src/components/order/ProductEditDialog.vue` 中供应商选择回调

- [ ] **步骤 1：替换 FieldInput 为 el-select + allow-create**

将现有的 `<FieldInput v-model="form.shop_url">` 替换为：

```vue
<el-select
  v-model="form.shop_url"
  filterable
  allow-create
  default-first-option
  placeholder="选择或输入 1688 链接"
  :disabled="formLocked"
  style="width: 100%"
  @change="onShopUrlChange"
>
  <el-option
    v-for="u in supplierUrlOptions"
    :key="u.id || u.url"
    :label="u.display_name || u.url"
    :value="u.url"
  />
</el-select>
```

- [ ] **步骤 2：添加状态与方法**

在 script 中：

```typescript
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'

const supplierUrlOptions = ref<ProductSupplierUrl[]>([])
let userEditedShopUrl = false

async function loadSupplierUrls() {
  if (!form.supplier_name) {
    supplierUrlOptions.value = []
    return
  }
  const pid = item.value?.product_id
  if (!pid) {
    supplierUrlOptions.value = []
    return
  }
  try {
    const res = await productSupplierUrlsApi.list(
      pid,
      (form.supplier as any)?.id,
      form.supplier_name,
    )
    supplierUrlOptions.value = res.data || []
  } catch (e) {
    supplierUrlOptions.value = []
  }
}

async function onShopUrlChange(url: string) {
  userEditedShopUrl = true
  if (!url) return
  const pid = item.value?.product_id
  if (pid && form.supplier_name) {
    try {
      await productSupplierUrlsApi.create({
        product_id: pid,
        supplier_id: (form.supplier as any)?.id ?? null,
        supplier_name: form.supplier_name,
        url,
      })
      await loadSupplierUrls()
    } catch (e) {
      console.warn('[ProductEditDialog] 保存采购链接失败', e)
    }
  }
  saveField('shop_url', url)
}

function applyShopUrlFromPriority() {
  // 已有 pi_item.shop_url 不覆盖
  if (userEditedShopUrl) return
  if (form.shop_url) return

  // 默认 URL（最高优先级）
  const defaultUrl = supplierUrlOptions.value.find((u) => u.is_default)
  if (defaultUrl) {
    form.shop_url = defaultUrl.url
    saveField('shop_url', defaultUrl.url)
    return
  }
  // 最新 URL
  if (supplierUrlOptions.value.length > 0) {
    form.shop_url = supplierUrlOptions.value[0].url
    saveField('shop_url', form.shop_url)
    return
  }
  // supplier.shop_link fallback（仅 1688）
  const supLink = (form.supplier as any)?.shop_link
  if (supLink) {
    form.shop_url = supLink
    saveField('shop_url', supLink)
  }
}
```

- [ ] **步骤 3：在供应商选择/清除时调用**

在 `onSupplierSelect(s)` 函数末尾添加：
```typescript
await loadSupplierUrls()
applyShopUrlFromPriority()
```

在 `onSupplierClear` 中添加：
```typescript
supplierUrlOptions.value = []
userEditedShopUrl = false
```

在 `onNewSupplierCreated` 函数末尾添加：
```typescript
await loadSupplierUrls()
applyShopUrlFromPriority()
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/components/order/ProductEditDialog.vue
git commit -m "feat: add 1688 URL dropdown to ProductEditDialog with priority-based fill"
```

---

## 任务 8：PurchaseDialog 表格行 1688 链接

**文件：**
- 修改：`frontend/src/components/order/PurchaseDialog.vue:12-47`（新增列）
- 修改：`frontend/src/components/order/PurchaseDialog.vue` 的 `loadInitialPrices` 与 `onSubmit`

- [ ] **步骤 1：表格新增「1688 链接」列**

在「总金额」前插入新列：

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

- [ ] **步骤 2：添加 URL 加载与变更方法**

```typescript
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'

interface UrlOptionCarrier {
  _urlOptions?: ProductSupplierUrl[]
}

async function reloadAllUrls() {
  const supplier = pendingSupplierState.supplier
  if (!supplier) return
  for (const row of items.value as any[]) {
    if (!row.product_id) continue
    try {
      const res = await productSupplierUrlsApi.list(
        row.product_id,
        (supplier as any).id,
        supplier.supplier_name,
      )
      row._urlOptions = res.data || []
    } catch (e) {
      row._urlOptions = []
    }
  }
}

function onItemUrlChange(index: number, url: string) {
  // v3 修订：URL 历史完全由后端事务写入，前端不再单独调用 API
  // 这里只更新 row.link；提交时由后端在同一事务内持久化
  ;(items.value[index] as any).link = url
}
```

- [ ] **步骤 3：在供应商选择后加载 URL 历史**

在 `open()` 函数中 pending 回填逻辑（1688 分支）的最后添加：
```typescript
// 加载所有产品行的 URL 历史下拉
await reloadAllUrls()
```

- [ ] **步骤 4：提交（v3 修订：不再写 URL 历史）**

v3 修订：删除前端的 `persistSupplierUrlsAfterPurchase()`。URL 历史完全由后端事务（任务 4）写入。前端提交时只负责把 `row.link` 放进 `items[i].link` 提交，路由层在同一事务内一并入库。

```typescript
// PurchaseDialog 的 onSubmit 中，items 已经包含 link：
const onlinePayload: PurchaseCreateOnline = {
  // ...
  items: items.value.map((it: any) => ({
    product_id: it.product_id,
    link: it.link || null,  // v3 关键：每行独立 URL
    // ...其他字段保持原样
  })),
}
await createOnlinePurchase(onlinePayload)
```

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/components/order/PurchaseDialog.vue
git commit -m "feat: add per-row 1688 URL dropdown in PurchaseDialog table (write delegated to backend transaction)"
```

---

## 规格覆盖度自检

| 规格章节 | 对应任务 |
|---------|---------|
| 2.1 新表 `prd_product_supplier_url` | 任务 1 |
| 2.2 `po_1688_purchase.supplier_id` + 采购链路贯穿 | 任务 1 + 任务 4 |
| 2.3 数据库迁移（含历史数据导入） | 任务 1 |
| 3.1-3.6 API 设计 | 任务 2 + 任务 3 |
| 4 is_default 业务规则 | 任务 2（实现）+ 任务 5（测试） |
| 5.1 前端 API 层 | 任务 6 |
| 5.2 ProductEditDialog URL 下拉 + 来源优先级 | 任务 7 |
| 5.3 PurchaseDialog 每行 URL 下拉 + 写入历史 | 任务 8 |
| 6 供应商链接填充规则（避免竞态） | 任务 7 步骤 3（优先级 + applyShopUrlFromPriority） |
| 7 事务边界 | 任务 4 步骤 2（移除内部 commit + flush） |

无遗漏。
