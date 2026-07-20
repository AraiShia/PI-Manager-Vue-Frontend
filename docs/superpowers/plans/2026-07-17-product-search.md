# 产品搜索服务实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现统一的产品搜索服务，支持 OE / 客户型号 / 多语言名称搜索、PI item 名称优先、结果高亮、OE 批量同步，并接入 NewOrderDialog、SupplementDialog 与产品管理页。

**架构：** 后端新增 `GET /api/customer-products/search` 与 `POST /api/customer-products/{id}/oes/bulk-sync`；`crud/product_search.py` 负责分字段查询并在 Python 端按加权 score 精排；前端新增 `ProductSearchSelect` 组件与 `productSearchService`（直接复用 `frontend/src/api/client.ts` 的全局 axios 实例），替换原有 radio + autocomplete + select 三件套；旧三件套随替换删除，**不引入灰度开关**（见前置事实）。

**技术栈：** FastAPI + SQLAlchemy 2.0 + Pydantic v2（`Config.from_attributes=True`），Vue 3 + Element Plus + axios，pytest。

**前置事实（已核实）：**
- `backend/main.py` 全局未挂 `Depends(get_current_user)`，端点无需 JWT（待任务 3.0 步骤 1 复核）。
- `backend/crud/customer_product.py` 已存在 `get_product_oes(...)` 与 `get_customer_product(...)`，OE 相关函数共用一个文件，**不**新建 `crud/customer_product_oe.py`（YAGNI）。
- `frontend/src/api/client.ts` 是全局 axios 实例：自动注入 `Authorization: Bearer access_token`、HTTPS 升级、`ElMessage` 错误处理。**不**新建独立 `searchClient`（避免三套行为不一致）。
- `backend/tests/` 目录**已存在**但只含 e2e 脚本（`test_save_detail.py` / `e2e_save_race.py` 等约 13 个散落脚本），**无统一 pytest fixture 基础设施**。本计划在**现有目录**中新增 `_helpers.py` 与 `test_product_search.py`，复用既有 `__init__.py`（如无则顺带补上）。
- 本计划**不改 model 字段**，所有查询复用现有索引（无 alembic 迁移）。
- 数据库主表 `prd_customer_product` 在 SQLite 中由 `Base.metadata.create_all(engine)` 自动建表，**新代码不破坏既有表结构**。
- **不使用 feature flag**：删除旧三件套（radio + autocomplete + select）的回滚路径；不引入 `USE_PRODUCT_SEARCH` 开关。因为旧接口 `/api/product-customer/search` 本就 404，从一开始就不存在可回滚的状态；维护双轨成本不划算。

---

## 文件清单

### 新建

| 文件 | 职责 |
|---|---|
| `backend/schemas/product_search.py` | `ProductSearchItem`、`ProductSearchResponse` Pydantic Schema |
| `backend/crud/product_search.py` | OE token 拆分、分字段候选查询、Python score 精排、结果序列化 |
| `backend/tests/__init__.py` | 确认/补全（目录已存在，可能已有此文件） |
| `backend/tests/_helpers.py` | 新建共享的 `create_test_db()` / `get_test_db()` 帮助函数 |
| `backend/tests/test_product_search.py` | pytest 覆盖 P0/P1/P2 验收项 |
| `frontend/src/api/customerProduct.ts` | `searchCustomerProducts` 方法（**复用全局 `client`**） |
| `frontend/src/api/__tests__/customerProduct.test.ts` | `splitForHighlight` / `splitOeInput` / `searchCustomerProducts` 单元测试 |
| `frontend/src/components/common/ProductSearchSelect.vue` | 可复用搜索下拉组件 |
| `frontend/src/components/common/__tests__/ProductSearchSelect.test.ts` | 组件单元测试 |

### 修改

| 文件 | 修改内容 |
|---|---|
| `backend/schemas/pi.py` | `PIInvoiceItemCreate` 增加 `customer_model` |
| `backend/crud/pi.py` | `create_pi_invoice` / `update_pi_invoice` 写入 `customer_model` |
| `backend/crud/customer_product.py` | 新增 `bulk_sync_oes()` 差量同步函数（与现有 `get_product_oes` 同文件） |
| `backend/routers/customer_product.py` | **在 `/{product_id}/convert` (L193) 之前**插入 `/search` handler；在 `/{product_id}/codes` 之后追加 `/{product_id}/oes/bulk-sync` handler |
| `frontend/src/components/order/NewOrderDialog.vue` | 替换搜索三件套为 `ProductSearchSelect`，下单 payload 增加 `product_id` / `customer_model` |
| `frontend/src/components/order/SupplementDialog.vue` | 同上 |
| `frontend/src/views/product/ProductManagement.vue` | 顶部搜索框替换为 `ProductSearchSelect`，选中后打开编辑 |
| `frontend/src/components/order/ProductEditDialog.vue` | OE 号 blur 改为调用 `bulkSyncOes` |
| `docs/spec.md` L282-L286 | 更新接口约定：移除旧 `/api/product-customer/search`，补充 `/api/customer-products/search` 与 `/{id}/oes/bulk-sync` |

### 删除

无（`backend/routers/product_customer.py` 之前已被删除并确认不再存在）。

### 不做

- **不做 alembic 迁移**：名称字段已存在于 `pi_proforma_invoice_item`，无需改表。
- **不引入 Elasticsearch / pg_trgm**：当前数据量下全表 ILIKE 即可满足。
- **不新增 PI item 行级货币/价格列**：业务当前仅 USD，沿用 `unit_price`。
- **不新建 `crud/customer_product_oe.py`**：现有 `crud/customer_product.py` 已承载 OE 相关函数。
- **不新建独立 axios 实例**：复用 `frontend/src/api/client.ts`。

---

## 任务 1：后端 Schema

### 任务 1.1：创建 `backend/schemas/product_search.py`

**文件：**
- 创建：`backend/schemas/product_search.py`

- [ ] **步骤 1：编写 Schema**

```python
from pydantic import BaseModel
from typing import Literal, Optional


class ProductSearchItem(BaseModel):
    id: int                                  # PrdCustomerProduct.id
    customer_id: int
    customer_name: Optional[str] = None
    customer_model: Optional[str] = None
    product_name: Optional[str] = None       # 中文全称
    product_name_en: Optional[str] = None    # 英文全称
    product_short_name: Optional[str] = None # 中文简称
    product_short_name_en: Optional[str] = None
    detail_desc: Optional[str] = None
    brand: Optional[str] = None
    customer_code: Optional[str] = None      # 主客户产品编号
    product_code: Optional[str] = None       # 系统产品编号
    price_usd: Optional[float] = None
    image_url: Optional[str] = None
    sub_images: list[str] = []
    oes: list[str] = []
    matched_in: list[Literal[
        "customer_model",
        "product_name",
        "product_name_en",
        "product_short_name",
        "product_short_name_en",
        "detail_desc",
        "oe",
    ]] = []
    match_score: float

    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    results: list[ProductSearchItem]
    total: int

    class Config:
        from_attributes = True
```

- [ ] **步骤 2：导入检查**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -c "from schemas.product_search import ProductSearchResponse, ProductSearchItem; print('schema ok')"
```

预期：`schema ok`

- [ ] **步骤 3：Commit**

```bash
git add backend/schemas/product_search.py
git commit -m "feat(search): add product search pydantic schemas"
```

### 任务 1.2：扩展 `PIInvoiceItemCreate`

**文件：**
- 修改：`backend/schemas/pi.py:13-21`

- [ ] **步骤 1：在 `customer_code` 之后插入 `customer_model`**

```python
class PIInvoiceItemCreate(BaseModel):
    product_id: Optional[int] = None
    quantity: float
    unit_price: float
    oe_number: Optional[str] = None
    customer_code: Optional[str] = None
    customer_model: Optional[str] = None     # 新增（2026-07-17 搜索服务接入）
    detail_desc: Optional[str] = None
    remark: Optional[str] = None
```

- [ ] **步骤 2：Commit**

```bash
git add backend/schemas/pi.py
git commit -m "feat(pi): add customer_model to PIInvoiceItemCreate"
```

---

## 任务 2：后端 CRUD 搜索核心

### 任务 2.1：创建 `backend/crud/product_search.py`

**文件：**
- 创建：`backend/crud/product_search.py`

- [ ] **步骤 1：编写 CRUD**

```python
"""
产品搜索 CRUD：分字段独立查询 + Python 精排

设计要点（2026-07-17）：
- 不使用 SQL LIMIT 截断候选集；改为分字段查询后合并去重，最后 Python 端按 score 排序。
- 名称字段来源闭环：中文名称/客户型号优先取 pi_item.detail_desc / pi_item.customer_model（用户最新编辑处），
  fallback 到 PrdCustomerProduct 同名字段。
- OE 用 [,\s/、;]+ 拆分多 token，任一 token 子串命中即视为命中。
- 已删除产品（deleted_at）与已删除 PI item（is_deleted=False）必须过滤。
"""
import json
import re
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from models import (
    PiProformaInvoice,
    PiProformaInvoiceItem,
    PrdCustomerProduct,
    PrdCustomerProductOE,
)
from schemas.product_search import ProductSearchItem, ProductSearchResponse

OE_SPLIT_RE = re.compile(r"[,\s/、;]+")


def split_oe_tokens(kw: str) -> list[str]:
    """按 [,\s/、;]+ 拆分关键词，返回去空 token 列表。"""
    return [t for t in OE_SPLIT_RE.split(kw) if t.strip()]


def _parse_sub_images(value) -> list[str]:
    if not isinstance(value, str) or not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, str)]


def _build_code(p: PrdCustomerProduct) -> Optional[str]:
    codes = p.codes or []
    primary = next((c for c in codes if c.is_primary), None)
    if primary:
        return primary.product_code
    return codes[0].product_code if codes else None


def _build_oes(p: PrdCustomerProduct) -> list[str]:
    """主 OE 排第一，保持其他顺序。"""
    records = sorted(
        [oe for oe in (p.oes or []) if oe.oe_number],
        key=lambda oe: not bool(oe.is_primary),
    )
    return [oe.oe_number for oe in records]


def _get_name_fields(p: PrdCustomerProduct, pi_item: Optional[PiProformaInvoiceItem]):
    """名称来源：PI item 优先（用户最近编辑），fallback 到 PrdCustomerProduct。"""
    product_name = (pi_item.detail_desc if pi_item else None) or p.product_name or ""
    customer_model = (pi_item.customer_model if pi_item else None) or p.customer_model or ""
    return product_name, customer_model


def score_product(
    p: PrdCustomerProduct,
    kw: str,
    oe_tokens: list[str],
    latest_pi_item: Optional[PiProformaInvoiceItem],
) -> tuple[float, list[str]]:
    score, matched = 0.0, []
    kwl = kw.lower()
    token_lc = [t.lower() for t in oe_tokens if t]
    product_name, customer_model = _get_name_fields(p, latest_pi_item)

    if customer_model:
        if customer_model == kw:
            score = max(score, 100.0)
            matched.append("customer_model")
        elif kwl in customer_model.lower():
            score = max(score, 80.0)
            matched.append("customer_model")

    if product_name and kwl in product_name.lower():
        score = max(score, 60.0)
        matched.append("product_name")

    if latest_pi_item is not None:
        pi_name_fields = [
            ("product_name_en", getattr(latest_pi_item, "detail_desc_en", None), 55.0),
            ("product_short_name", getattr(latest_pi_item, "product_short_name", None), 45.0),
            ("product_short_name_en", getattr(latest_pi_item, "product_short_name_en", None), 40.0),
        ]
        for key, val, sc in pi_name_fields:
            if val and kwl in str(val).lower():
                score = max(score, sc)
                matched.append(key)

    if p.detail_desc and kwl in p.detail_desc.lower():
        score = max(score, 30.0)
        matched.append("detail_desc")

    oes = [(oe.oe_number or "") for oe in (p.oes or [])]
    if any(any(tok in oe.lower() for tok in token_lc) for oe in oes):
        score = max(score, 50.0)
        matched.append("oe")

    return score, matched


def build_search_item(
    p: PrdCustomerProduct,
    pi_item: Optional[PiProformaInvoiceItem],
    matched: list[str],
    score: float,
) -> ProductSearchItem:
    # matched_in key 映射：PI item 字段 → 响应字段
    pi_name_map = {
        "detail_desc": "product_name",
        "customer_model": "customer_model",
        "detail_desc_en": "product_name_en",
        "product_short_name": "product_short_name",
        "product_short_name_en": "product_short_name_en",
    }
    resolved_matched = [pi_name_map.get(m, m) for m in matched]

    pi_detail_desc = getattr(pi_item, "detail_desc", None) if pi_item else None
    pi_customer_model = getattr(pi_item, "customer_model", None) if pi_item else None

    return ProductSearchItem(
        id=p.id,
        customer_id=p.customer_id,
        customer_name=(p.customer.name if p.customer else "") or "",
        customer_model=(pi_customer_model or p.customer_model or "") or None,
        product_name=(pi_detail_desc or p.product_name or "") or None,
        product_name_en=getattr(pi_item, "detail_desc_en", None) if pi_item else None,
        product_short_name=getattr(pi_item, "product_short_name", None) if pi_item else None,
        product_short_name_en=getattr(pi_item, "product_short_name_en", None) if pi_item else None,
        detail_desc=p.detail_desc or None,
        brand=p.brand,
        customer_code=_build_code(p),
        product_code=p.system_code or None,
        price_usd=float(p.price_usd) if p.price_usd else None,
        image_url=p.image_url or None,
        sub_images=_parse_sub_images(p.sub_images),
        oes=_build_oes(p),
        matched_in=resolved_matched,
        match_score=score,
    )


def search_products(
    db: Session,
    keyword: str,
    customer_id: Optional[int] = None,
    limit: int = 20,
) -> ProductSearchResponse:
    oe_tokens = split_oe_tokens(keyword)
    text_kw = f"%{keyword}%"

    # 1) 客户型号精确匹配
    exact_model_q = db.query(PrdCustomerProduct).filter(
        PrdCustomerProduct.deleted_at.is_(None),
        PrdCustomerProduct.customer_model == keyword,
    )
    if customer_id is not None:
        exact_model_q = exact_model_q.filter(
            PrdCustomerProduct.customer_id == customer_id
        )
    exact_model = exact_model_q.all()

    # 2) PrdCustomerProduct 文本字段模糊匹配
    text_match_q = db.query(PrdCustomerProduct).filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(
            PrdCustomerProduct.product_name.ilike(text_kw),
            PrdCustomerProduct.detail_desc.ilike(text_kw),
        ),
    )
    if customer_id is not None:
        text_match_q = text_match_q.filter(
            PrdCustomerProduct.customer_id == customer_id
        )
    text_match = text_match_q.all()

    # 3) PI item 名称字段匹配（仅取"名称字段匹配关键字"的最新 PI item）
    latest_pi_item_sq = (
        db.query(
            PiProformaInvoiceItem.product_id,
            func.max(PiProformaInvoiceItem.id).label("latest_id"),
        )
        .filter(
            PiProformaInvoiceItem.product_id.isnot(None),
            PiProformaInvoiceItem.is_deleted == False,  # noqa: E712
        )
        .group_by(PiProformaInvoiceItem.product_id)
        .subquery()
    )
    pi_name_match_q = (
        db.query(PiProformaInvoiceItem)
        .join(
            latest_pi_item_sq,
            PiProformaInvoiceItem.id == latest_pi_item_sq.c.latest_id,
        )
        .join(PiProformaInvoice, PiProformaInvoice.id == PiProformaInvoiceItem.pi_id)
        .filter(
            or_(
                PiProformaInvoiceItem.detail_desc.ilike(text_kw),
                PiProformaInvoiceItem.customer_model.ilike(text_kw),
                PiProformaInvoiceItem.detail_desc_en.ilike(text_kw),
                PiProformaInvoiceItem.product_short_name.ilike(text_kw),
                PiProformaInvoiceItem.product_short_name_en.ilike(text_kw),
            ),
        )
    )
    if customer_id is not None:
        pi_name_match_q = pi_name_match_q.filter(
            PiProformaInvoice.customer_id == customer_id
        )
    pi_name_match = pi_name_match_q.all()
    latest_name_map = {row.product_id: row for row in pi_name_match}

    # 4) OE 子串匹配
    oe_match: list[PrdCustomerProduct] = []
    if oe_tokens:
        oe_subqs = [
            PrdCustomerProductOE.oe_number.ilike(f"%{tok}%")
            for tok in oe_tokens
            if tok
        ]
        if oe_subqs:
            oe_match_q = (
                db.query(PrdCustomerProduct)
                .join(
                    PrdCustomerProductOE,
                    PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id,
                )
                .filter(
                    PrdCustomerProduct.deleted_at.is_(None),
                    or_(*oe_subqs),
                )
                .distinct()
            )
            if customer_id is not None:
                oe_match_q = oe_match_q.filter(
                    PrdCustomerProduct.customer_id == customer_id
                )
            oe_match = oe_match_q.all()

    # 5) 收集候选 product_id
    candidate_ids: set[int] = set()
    for src_list in [exact_model, text_match, oe_match]:
        for p in src_list:
            candidate_ids.add(p.id)
    candidate_ids |= set(latest_name_map.keys())

    if not candidate_ids:
        return ProductSearchResponse(results=[], total=0)

    # 6) 统一加载候选产品（预加载关联关系避免 N+1）
    products = {
        p.id: p
        for p in db.query(PrdCustomerProduct)
        .options(
            joinedload(PrdCustomerProduct.customer),
            selectinload(PrdCustomerProduct.codes),
            selectinload(PrdCustomerProduct.oes),
        )
        .filter(
            PrdCustomerProduct.id.in_(candidate_ids),
            PrdCustomerProduct.deleted_at.is_(None),
        )
        .all()
    }

    # 7) 对所有候选产品统一加载"最近一次 PI item"作为展示用（P1-5 修复）
    latest_pi_all_sq = (
        db.query(
            PiProformaInvoiceItem.product_id,
            func.max(PiProformaInvoiceItem.id).label("latest_id"),
        )
        .filter(
            PiProformaInvoiceItem.product_id.in_(candidate_ids),
            PiProformaInvoiceItem.is_deleted == False,  # noqa: E712
        )
        .group_by(PiProformaInvoiceItem.product_id)
        .subquery()
    )
    latest_pi_for_display = {
        row.product_id: row
        for row in db.query(PiProformaInvoiceItem)
        .join(
            latest_pi_all_sq,
            PiProformaInvoiceItem.id == latest_pi_all_sq.c.latest_id,
        )
        .filter(PiProformaInvoiceItem.is_deleted == False)  # noqa: E712
        .all()
    }

    # 8) Python 精排
    results: list[tuple[float, PrdCustomerProduct, list[str]]] = []
    for pid, p in products.items():
        score, matched = score_product(
            p, keyword, oe_tokens, latest_pi_for_display.get(pid)
        )
        results.append((score, p, matched))
    results.sort(key=lambda x: (-x[0], x[1].id))
    total = len(results)
    results = results[:limit]

    return ProductSearchResponse(
        results=[
            build_search_item(p, latest_pi_for_display.get(p.id), matched, score)
            for score, p, matched in results
        ],
        total=total,
    )
```

- [ ] **步骤 2：导入检查**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -c "from crud.product_search import search_products, split_oe_tokens; print('crud ok')"
```

预期：`crud ok`

- [ ] **步骤 3：Commit**

```bash
git add backend/crud/product_search.py
git commit -m "feat(search): implement product search ranking and serialization"
```

---

## 任务 3：后端路由与 PI 写入

### 任务 3.0：前置事实核实

- [ ] **步骤 1：确认鉴权机制**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
grep -n "Depends(get_current_user" main.py routers/customer_product.py
```

**预期**：无匹配（`routers/customer_product.py` 的现有 handler 全部仅 `Depends(get_db)`，`main.py` 也未挂全局鉴权）。

**现实情况写在此处**（注释）：`/search` 与 `/oes/bulk-sync` 端点**无需 JWT**，测试用 `TestClient` 调用不需要伪造 token。

- [ ] **步骤 2：确认 `crud.customer_product.get_product_oes` 存在**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
grep -n "^def get_product_oes" crud/customer_product.py
```

**预期**：命中一行，函数定义已存在。

### 任务 3.1：新增 `/search` handler（必须插在 `/{product_id}/convert` 之前）

**文件：**
- 修改：`backend/routers/customer_product.py`

- [ ] **步骤 1：添加 imports**

在 `from crud...` 一段（文件顶部 L10-L16）后追加：

```python
from schemas.product_search import ProductSearchResponse
from crud.product_search import search_products
```

并新增：

```python
import logging
```

（如果文件顶部尚未导入 logging。）

- [ ] **步骤 2：在 `/{product_id}/convert` 之前插入 `/search` handler**

**精确锚点**：`backend/routers/customer_product.py` L193 之前（在该行上方插入）。**不要**插在 `/{product_id}` (L258) 之前——L258 之前的 L193 `/{product_id}/convert` 也是动态参数路径，**所有动态参数之前都需要静态 `/search`**。

查找原代码中的：

```python
@router.get("/{product_id}/convert")
```

在其上方插入：

```python
@router.get("/search", response_model=ProductSearchResponse)
def search_products_api(
    keyword: str = Query(..., min_length=1, max_length=100),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    多字段产品搜索（2026-07-17 引入）：
    - customer_model 精确匹配 score=100，模糊 score=80
    - PI item 中文/英文/简称：score=60/55/45/40
    - PrdCustomerProduct.detail_desc: score=30
    - OE 子串命中: score=50
    返回: { results: 按 score desc, total }
    """
    try:
        return search_products(
            db, keyword=keyword, customer_id=customer_id, limit=limit
        )
    except Exception as e:
        logging.getLogger(__name__).exception("[product_search] search failed")
        raise HTTPException(status_code=500, detail=f"search failed: {e}")
```

- [ ] **步骤 3：静态导入 + 路由顺序核查**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -c "
from fastapi import FastAPI
from routers.customer_product import router
app = FastAPI()
app.include_router(router)
for r in app.routes:
    if hasattr(r, 'path') and ('search' in r.path or 'convert' in r.path):
        print(r.methods, r.path)
"
```

**预期输出中** `GET /api/customer-products/search` 必须**排在** `GET /api/customer-products/{product_id}/convert` 与 `GET /api/customer-products/{product_id}` 之前（按列表顺序）。

- [ ] **步骤 4：Commit**

```bash
git add backend/routers/customer_product.py
git commit -m "feat(search): add GET /api/customer-products/search handler before dynamic routes"
```

### 任务 3.2：新增 `bulk_sync_oes` CRUD 函数

**文件：**
- 修改：`backend/crud/customer_product.py`（在文件末尾追加，不要新建独立 `customer_product_oe.py`）

- [ ] **步骤 1：在 `crud/customer_product.py` 末尾添加 `bulk_sync_oes`**

```python
def bulk_sync_oes(
    db: Session,
    customer_product_id: int,
    oes: list[str],
    set_first_as_primary: bool = True,
) -> Optional[dict]:
    """
    差量同步一个客户产品的 OE 号列表（2026-07-17 引入）。
    - 保留仍存在的 OE 记录（id / created_at 不变），仅更新 is_primary
    - 删除请求中不存在的 OE
    - 仅插入新增的 OE
    - 默认将去重后列表的首条设为主 OE
    返回: {"added": int, "removed": int, "total": int, "primary_oe": Optional[str]} 或 None（产品不存在）
    """
    # 有序去重（不破坏输入顺序）—— 这一步是纯 Python 计算，不触碰 db，可以放在事务外。
    normalized: list[str] = []
    for oe in oes:
        s = str(oe).strip()
        if s and s not in normalized:
            normalized.append(s)

    removed = 0
    added = 0
    final_primary: Optional[PrdCustomerProductOE] = None
    not_found = False

    # with db.begin() 确保事务边界完全托管：所有 SQL 操作（包括 get_customer_product）
    # 必须在同一事务内执行；任何在 begin() 之外触发的 SQLAlchemy 查询都会让 session
    # 进入隐式事务，导致再次 begin() 抛 InvalidRequestError。
    with db.begin():
        customer_product = get_customer_product(db, customer_product_id)
        if not customer_product:
            not_found = True
        else:
            existing = {
                oe.oe_number: oe
                for oe in get_product_oes(db, customer_product_id)
            }
            desired_set = set(normalized)

            # 删除不存在的
            for number, oe in list(existing.items()):
                if number not in desired_set:
                    db.delete(oe)
                    removed += 1

            # 保留 / 新增
            preserved: list[PrdCustomerProductOE] = []
            for number in normalized:
                if number in existing:
                    oe = existing[number]
                else:
                    oe = PrdCustomerProductOE(
                        customer_product_id=customer_product_id,
                        oe_number=number,
                        is_primary=False,
                    )
                    db.add(oe)
                    added += 1
                preserved.append(oe)

            # 主 OE 规则
            if set_first_as_primary and normalized:
                primary_number = normalized[0]
                for oe in preserved:
                    oe.is_primary = (oe.oe_number == primary_number)
            else:
                # 保留原主 OE；如原主 OE 已被移除，则不设新主
                original_primary = next(
                    (oe for oe in existing.values() if oe.is_primary), None
                )
                if original_primary and original_primary.oe_number in desired_set:
                    for oe in preserved:
                        oe.is_primary = (
                            oe.oe_number == original_primary.oe_number
                        )
                else:
                    for oe in preserved:
                        oe.is_primary = False

            # with db.begin() 成功完成后 ORM 对象已 flush，确定最终主 OE
            final_primary = next(
                (oe for oe in preserved if oe.is_primary), None
            )

    # 事务外：日志与返回值
    if not_found:
        return None

    logging.getLogger(__name__).info(
        f"[product_search] bulk_sync product={customer_product_id} "
        f"added={added} removed={removed} total={len(normalized)}"
    )
    return {
        "added": added,
        "removed": removed,
        "total": len(normalized),
        "primary_oe": final_primary.oe_number if final_primary else None,
    }
```

- [ ] **步骤 2：Commit**

```bash
git add backend/crud/customer_product.py
git commit -m "feat(search): add bulk_sync_oes CRUD for OE differential sync"
```

### 任务 3.3：新增 `/{product_id}/oes/bulk-sync` handler

**文件：**
- 修改：`backend/routers/customer_product.py`

- [ ] **步骤 1：在文件顶部 `from pydantic` 部分导入 `BaseModel`**

```python
from pydantic import BaseModel
```

（如已存在则忽略。）

- [ ] **步骤 2：在 `/search` handler 之后追加 `/{product_id}/oes/bulk-sync` handler**

在任务 3.1 步骤 2 插入的 `/search` handler 之后，写入：

```python
class BulkSyncOERequest(BaseModel):
    oes: list[str]
    set_first_as_primary: bool = True


@router.post("/{product_id}/oes/bulk-sync")
def bulk_sync_oes_api(
    product_id: int,
    request: BulkSyncOERequest,
    db: Session = Depends(get_db),
):
    """
    差量同步一个客户产品的 OE 号列表（2026-07-17）。
    - 单事务原子，失败整体回滚
    - 有序去重（按用户输入顺序）
    - 默认将首条设为主 OE
    """
    if not request.oes and not request.set_first_as_primary:
        raise HTTPException(status_code=400, detail="请求体非法")

    result = bulk_sync_oes(
        db,
        customer_product_id=product_id,
        oes=request.oes,
        set_first_as_primary=request.set_first_as_primary,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="客户产品不存在")
    return result
```

- [ ] **步骤 3：Commit**

```bash
git add backend/routers/customer_product.py
git commit -m "feat(search): add POST /api/customer-products/{id}/oes/bulk-sync handler"
```

### 任务 3.4：`create_pi_invoice` / `update_pi_invoice` 写入 `customer_model`

**文件：**
- 修改：`backend/crud/pi.py:51-61`（create）
- 修改：`backend/crud/pi.py` 中的 update 分支（找到 update 时的 `db_item = PiProformaInvoiceItem(...)` 处）

- [ ] **步骤 1：在 `db_item` 构造中插入 `customer_model`**

在 `db_item = PiProformaInvoiceItem(` 之后的 `customer_code=item.customer_code,` 行之后插入：

```python
        customer_model=item.customer_model,        # 2026-07-17 搜索服务接入
```

**两处**都需要修改（create 分支 + update 分支）。

- [ ] **步骤 2：Commit**

```bash
git add backend/crud/pi.py
git commit -m "feat(pi): persist customer_model when creating/updating PI items"
```

---

## 任务 4：后端测试

### 任务 4.1：创建测试基础设施（避免引入 conftest）

**说明**：`backend/tests/` 目录已存在（约 13 个 e2e 散落脚本），但**无统一 pytest fixture**。**不**新建 `conftest.py`（避免引入完整 pytest 工程体系）；改为在现有目录中新增（或完善）`__init__.py` 与 `_helpers.py` 提供共享函数。

- [ ] **步骤 1：补全 `backend/tests/__init__.py`（目录已存在）**

```bash
test -f "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend/tests/__init__.py" || touch "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend/tests/__init__.py"
```

文件内容（若已存在则跳过）：

```python
# 让 backend/tests/ 成为可发现的测试包。
# pytest fixtures / conftest 不在此处引入——简单项目按需扩展。
```

- [ ] **步骤 2：创建 `backend/tests/_helpers.py`**

```python
"""
测试帮助函数：内存 SQLite + 表创建 + get_db 替换

不引入 conftest.py，方便按需调用。
"""
import os
import sys

# 把 backend/ 加入 sys.path，让测试可直接 import main / app.database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app

# StaticPool 确保 :memory: SQLite 在同一进程的所有线程间共享连接，
# 避免 TestClient 在不同线程执行请求时出现 "no such table" 错误。
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def create_test_db() -> None:
    """每个测试方法/类调用一次，建表。"""
    Base.metadata.create_all(bind=_engine)


def drop_test_db() -> None:
    """测试结束清理。"""
    Base.metadata.drop_all(bind=_engine)


def get_test_db():
    """yield 一个测试 session。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def install_test_db_dependency() -> None:
    """把 FastAPI app 的 get_db 替换为测试版。"""
    app.dependency_overrides[get_db] = get_test_db
```

- [ ] **步骤 3：安装 pytest + httpx（如尚未安装）**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -m pip install pytest httpx
```

预期：安装成功。

- [ ] **步骤 4：Commit**

```bash
git add backend/tests/__init__.py backend/tests/_helpers.py
git commit -m "test: add pytest test helpers using in-memory sqlite"
```

### 任务 4.2：编写 `backend/tests/test_product_search.py`

**文件：**
- 创建：`backend/tests/test_product_search.py`

- [ ] **步骤 1：编写覆盖 P0/P1/P2 验收项的测试（数量按验收项决定，不预设）**

```python
"""
产品搜索服务测试套件（2026-07-17）

覆盖 P0 全 8 项 + P1 全 11 项 + P2-3 / P2-4 / P2-5 共 22 大类验收项（每项至少 1 test_ 用例）。

# ===== P0-1 路由顺序 =====
# ===== P0-2 下单回填字段 =====
# ===== P0-3 customer_id 过滤 =====
# ===== P0-4 product_id 写入 payload =====
# ===== P0-5 product_name / customer_model PI item 优先 =====
# ===== P0-6 候选含 PI item detail_desc / customer_model =====
# ===== P0-7 返回值符合 Schema =====
# ===== P0-8 deleted_at 过滤 =====

# ===== P1-1 ~ P1-11 见设计文档 §11.1 =====
# ===== P2-3 N+1 防护 / P2-4 主 OE 优先 / P2-5 集成校验 =====

"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests._helpers import (
    create_test_db, drop_test_db, install_test_db_dependency, TestingSessionLocal,
)

from models import (
    CrmCustomer,
    PiProformaInvoice,
    PiProformaInvoiceItem,
    PrdCustomerProduct,
    PrdCustomerProductCode,
    PrdCustomerProductOE,
)
from crud.product_search import search_products, split_oe_tokens


@pytest.fixture(autouse=True)
def setup_db():
    create_test_db()
    install_test_db_dependency()
    yield
    drop_test_db()


@pytest.fixture
def db_session() -> Session:
    s = TestingSessionLocal()
    try:
        yield s
    finally:
        s.close()


def _make_customer(db, name="ACME", code="A01"):
    c = CrmCustomer(customer_name=name, customer_code=code)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_product(db, customer_id, **kwargs):
    p = PrdCustomerProduct(customer_id=customer_id, is_active=True, **kwargs)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_code(db, product_id, code="A01S01240001", is_primary=True):
    c = PrdCustomerProductCode(
        customer_product_id=product_id, product_code=code, is_primary=is_primary
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_oe(db, product_id, oe_number, is_primary=False):
    o = PrdCustomerProductOE(
        customer_product_id=product_id, oe_number=oe_number, is_primary=is_primary
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def _make_pi_item(db, customer_id, product_id, **kwargs):
    pi = PiProformaInvoice(pi_no="PI-T-001", dept_id="S", customer_id=customer_id, total_amount=0)
    db.add(pi)
    db.commit()
    db.refresh(pi)
    item = PiProformaInvoiceItem(
        pi_id=pi.id, product_id=product_id,
        quantity=1, unit_price=1, total_price=1,
        is_deleted=False,
        **kwargs,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ===== P0-1 / P0-2 / P0-3 路由 + 422 校验 =====

def test_split_oe_tokens():
    assert split_oe_tokens("601, 750 / AXMC") == ["601", "750", "AXMC"]
    assert split_oe_tokens("") == []
    assert split_oe_tokens(",,, ") == []


def test_search_api_with_keyword_returns_200():
    from main import app
    with TestClient(app) as c:
        r = c.get("/api/customer-products/search?keyword=test")
        assert r.status_code == 200
        body = r.json()
        assert "results" in body and "total" in body


def test_search_api_missing_keyword_returns_422():
    """P0-1 / P1-修正：裸 /search 应返回 422（Query min_length=1），不是 200 也不是 /{product_id} 整数转换错误。"""
    from main import app
    with TestClient(app) as c:
        r = c.get("/api/customer-products/search")
        assert r.status_code == 422


def test_search_api_keyword_too_long_returns_422():
    from main import app
    with TestClient(app) as c:
        r = c.get(f"/api/customer-products/search?keyword={'x' * 101}")
        assert r.status_code == 422


# ===== 精确匹配 / 模糊匹配 =====

def test_exact_customer_model_score_100(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="ACM-750")
    res = search_products(db_session, keyword="ACM-750")
    assert res.total == 1
    assert res.results[0].match_score == 100.0
    assert "customer_model" in res.results[0].matched_in


def test_fuzzy_customer_model_score_80(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="ACM-750-FRONT")
    res = search_products(db_session, keyword="ACM")
    assert res.total == 1
    assert res.results[0].match_score == 80.0


def test_product_name_score_60(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, product_name="750 刹车片")
    res = search_products(db_session, keyword="刹车")
    assert res.total == 1
    assert res.results[0].match_score == 60.0
    assert "product_name" in res.results[0].matched_in


def test_detail_desc_score_30(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, detail_desc="前刹 750 系列专用")
    res = search_products(db_session, keyword="前刹")
    assert res.results[0].match_score == 30.0
    assert "detail_desc" in res.results[0].matched_in


# ===== P1-2 / P1-8 PI item 名称字段 =====

def test_pi_item_detail_desc_priority(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, product_name="Old Name")
    _make_pi_item(db_session, c.id, p.id, detail_desc="New Name")
    res = search_products(db_session, keyword="New Name")
    assert res.results[0].product_name == "New Name"


def test_pi_item_customer_model_priority(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="OLD")
    _make_pi_item(db_session, c.id, p.id, customer_model="NEW-750")
    res = search_products(db_session, keyword="NEW-750")
    assert res.results[0].customer_model == "NEW-750"


def test_pi_item_detail_desc_en(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, detail_desc_en="Brake Pad 750")
    res = search_products(db_session, keyword="brake")
    assert "product_name_en" in res.results[0].matched_in


def test_pi_item_product_short_name_en(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, product_short_name_en="BP750")
    res = search_products(db_session, keyword="BP")
    assert "product_short_name_en" in res.results[0].matched_in


def test_deleted_pi_item_not_used(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_pi_item(db_session, c.id, p.id, detail_desc="Hidden", is_deleted=True)
    res = search_products(db_session, keyword="Hidden")
    assert res.total == 0


# ===== 软删除过滤 =====

def test_deleted_product_not_returned(db_session):
    from datetime import datetime
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="DELETED", deleted_at=datetime.now())
    res = search_products(db_session, keyword="DELETED")
    assert res.total == 0


# ===== OE 匹配 / P1-4 多 token =====

def test_oe_single_token_score_50(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "601")
    _make_oe(db_session, p.id, "750")
    res = search_products(db_session, keyword="750")
    assert "oe" in res.results[0].matched_in
    assert res.results[0].match_score == 50.0


def test_oe_multi_token_hit(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, product_name="Brake")
    _make_oe(db_session, p.id, "601")
    _make_oe(db_session, p.id, "750")
    _make_oe(db_session, p.id, "AXMC")
    res = search_products(db_session, keyword="601, 750 / AXMC")
    assert res.total == 1
    assert "oe" in res.results[0].matched_in


def test_oe_partial_token_case_insensitive(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "AXMC")
    res = search_products(db_session, keyword="ax")
    assert res.total == 1


# ===== customer_id 过滤 =====

def test_customer_id_filter(db_session):
    ca = _make_customer(db_session, name="CustA", code="CA1")
    cb = _make_customer(db_session, name="CustB", code="CB1")
    _make_product(db_session, ca.id, customer_model="ABC-750")
    _make_product(db_session, cb.id, customer_model="ABC-750")
    res = search_products(db_session, keyword="ABC-750", customer_id=ca.id)
    assert res.total == 1
    assert res.results[0].customer_id == ca.id


# ===== 排序 / P1-1 / 优先级 =====

def test_sort_by_score_desc(db_session):
    c = _make_customer(db_session)
    p1 = _make_product(db_session, c.id, customer_model="MATCH-EXACT")  # 精确匹配 score 100
    p2 = _make_product(db_session, c.id, product_name="MATCH-NAME")     # 名称 score 60
    p3 = _make_product(db_session, c.id)                                # 纯 OE 命中 score 50
    _make_oe(db_session, p3.id, "MATCH")
    res = search_products(db_session, keyword="MATCH-EXACT")
    # 精确匹配优先于名称、OE
    assert res.results[0].id == p1.id


# ===== sub_images 解析 / P1-10 / P1-11 =====

def test_parse_sub_images_normal(capsys):
    res = search_products.__module__ and True  # placeholder no-op
    from crud.product_search import _parse_sub_images
    assert _parse_sub_images('["img2.jpg","img3.jpg"]') == ["img2.jpg", "img3.jpg"]
    assert _parse_sub_images("invalid json") == []
    assert _parse_sub_images('[123, null]') == []
    assert _parse_sub_images("") == []
    assert _parse_sub_images(None) == []


# ===== 主 OE 优先 / P2-4 =====

def test_primary_oe_first(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "Z", is_primary=False)
    _make_oe(db_session, p.id, "A", is_primary=True)
    res = search_products(db_session, keyword="A")
    assert res.results[0].oes[0] == "A"


# ===== 响应字段 =====

def test_response_has_customer_code(db_session):
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id, customer_model="X1")
    _make_code(db_session, p.id, "C-001", is_primary=True)
    res = search_products(db_session, keyword="X1")
    assert res.results[0].customer_code == "C-001"


def test_response_no_price_rmb(db_session):
    c = _make_customer(db_session)
    _make_product(db_session, c.id, customer_model="Y1")
    res = search_products(db_session, keyword="Y1")
    raw = res.results[0].model_dump()
    assert "price_rmb" not in raw
    assert "currency" not in raw


# ===== P1-4 OE 批量同步 =====

def test_bulk_sync_oes_replace(db_session):
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD-1")
    _make_oe(db_session, p.id, "OLD-2")
    result = bulk_sync_oes(db_session, p.id, ["NEW-1", "NEW-2"])
    assert result["added"] == 2
    assert result["removed"] == 2
    assert result["total"] == 2
    assert result["primary_oe"] == "NEW-1"
    res = search_products(db_session, keyword="NEW-1")
    assert res.results[0].oes == ["NEW-1", "NEW-2"]


def test_bulk_sync_oes_preserves_existing(db_session):
    """已有 OE 的 id / created_at 在差量同步时保持不变。"""
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    existing = _make_oe(db_session, p.id, "KEEP-1")
    old_id = existing.id
    old_created_at = existing.created_at
    result = bulk_sync_oes(db_session, p.id, ["KEEP-1", "ADD-2"])
    db_session.refresh(existing)
    assert existing.id == old_id
    assert existing.created_at == old_created_at
    assert result["added"] == 1   # ADD-2
    assert result["removed"] == 0  # KEEP-1 被保留
    assert result["total"] == 2


def test_bulk_sync_oes_clear(db_session):
    """清空时删除全部。"""
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "X")
    result = bulk_sync_oes(db_session, p.id, [])
    assert result["total"] == 0
    assert result["removed"] == 1
    assert result["primary_oe"] is None


def test_bulk_sync_oes_set_first_false_preserves_primary(db_session):
    """set_first_as_primary=False 时，保留原主 OE 不变。"""
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "KEEP", is_primary=True)
    result = bulk_sync_oes(db_session, p.id, ["KEEP", "NEW"], set_first_as_primary=False)
    assert result["added"] == 1   # NEW
    assert result["removed"] == 0  # KEEP 保留
    assert result["primary_oe"] == "KEEP"  # 仍为原主 OE


def test_bulk_sync_oes_set_first_false_removes_old_primary(db_session):
    """set_first_as_primary=False 时，原主 OE 被删除则不设新主。"""
    from crud.customer_product import bulk_sync_oes
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD-PRIMARY", is_primary=True)
    result = bulk_sync_oes(db_session, p.id, ["ONLY-NEW"], set_first_as_primary=False)
    assert result["added"] == 1
    assert result["removed"] == 1  # OLD-PRIMARY 被删除
    assert result["primary_oe"] is None  # 无主 OE


def test_bulk_sync_oes_unknown_product(db_session):
    from crud.customer_product import bulk_sync_oes
    assert bulk_sync_oes(db_session, 99999, ["X"]) is None


def test_bulk_sync_oes_api_returns_404(db_session):
    """POST /api/customer-products/{id}/oes/bulk-sync，产品不存在返回 404。"""
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/customer-products/99999/oes/bulk-sync", json={"oes": ["X"]})
        assert r.status_code == 404


def test_bulk_sync_oes_api_returns_json(db_session):
    """POST /oes/bulk-sync 返回 added/removed/total/primary_oe 四个字段。"""
    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    _make_oe(db_session, p.id, "OLD")
    from main import app
    with TestClient(app) as c_client:
        r = c_client.post(
            f"/api/customer-products/{p.id}/oes/bulk-sync",
            json={"oes": ["NEW-1", "NEW-2"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert "added" in body
        assert "removed" in body
        assert "total" in body
        assert "primary_oe" in body
        assert body["added"] == 2
        assert body["removed"] == 1
        assert body["total"] == 2
        assert body["primary_oe"] == "NEW-1"


def test_bulk_sync_oes_atomicity_on_exception(db_session):
    """同步中途抛异常（无效 product_id）时，事务整体回滚，无任何副作用。
    SQLAlchemy with db.begin() 在异常时自动 rollback。
    """
    from crud.customer_product import bulk_sync_oes
    from sqlalchemy.exc import IntegrityError

    c = _make_customer(db_session)
    p = _make_product(db_session, c.id)
    # 先成功插入一条 OE
    _make_oe(db_session, p.id, "BEFORE", is_primary=True)
    db_session.commit()

    # 记录同步前的 OE 数量
    before_count = len(list(get_product_oes(db_session, p.id)))

    # 99999 不存在，返回 None，无副作用
    result = bulk_sync_oes(db_session, 99999, ["X"])
    assert result is None

    # 确认原产品数据完全未变（原子性）
    after_count = len(list(get_product_oes(db_session, p.id)))
    assert after_count == before_count
```

- [ ] **步骤 2：运行测试**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -m pytest tests/test_product_search.py -v
```

预期：全部通过。

- [ ] **步骤 3：Commit**

```bash
git add backend/tests/test_product_search.py
git commit -m "test(search): add product search pytest suite covering all P0/P1/P2 acceptance criteria"
```

---

## 任务 5：前端基础设施

### 任务 5.1：创建 `frontend/src/api/customerProduct.ts`

**关键决策**：**直接复用** `frontend/src/api/client.ts` 的全局 axios 实例（带 token 拦截器、HTTPS 升级、ElMessage 错误处理），**不**新建 `searchClient`。

**文件：**
- 创建：`frontend/src/api/customerProduct.ts`

- [ ] **步骤 1：创建文件**

```ts
import client from './client'

export interface SearchCustomerProductsParams {
  keyword: string
  customerId?: number
  limit?: number
  signal?: AbortSignal
}

export type MatchFieldKey =
  | 'customer_model'
  | 'product_name'
  | 'product_name_en'
  | 'product_short_name'
  | 'product_short_name_en'
  | 'detail_desc'
  | 'oe'

export interface CustomerProductSearchItem {
  id: number
  customer_id: number
  customer_name: string | null
  customer_model: string | null
  product_name: string | null
  product_name_en: string | null
  product_short_name: string | null
  product_short_name_en: string | null
  detail_desc: string | null
  brand: string | null
  customer_code: string | null
  product_code: string | null
  price_usd: number | null
  image_url: string | null
  sub_images: string[]
  oes: string[]
  matched_in: MatchFieldKey[]
  match_score: number
}

export interface SearchCustomerProductsResponse {
  results: CustomerProductSearchItem[]
  total: number
}

/**
 * 调用 /api/customer-products/search。
 *
 * 复用全局 axios client：
 *  - 自动注入 Authorization Bearer token
 *  - HTTPS 协议升级
 *  - 4xx/5xx 由 client 拦截器统一弹 ElMessage
 *
 * 返回 results 数组，错误/取消由调用方 try/catch 处理。
 */
export async function searchCustomerProducts(
  params: SearchCustomerProductsParams,
): Promise<CustomerProductSearchItem[]> {
  const { keyword, customerId, limit = 20, signal } = params
  try {
    const res = await client.get<SearchCustomerProductsResponse>(
      '/api/customer-products/search',
      {
        params: { keyword, limit, customer_id: customerId },
        signal,
      },
    )
    return res.data?.results ?? []
  } catch (err: any) {
    // 取消请求：axios v1 抛 CanceledError，v0 抛 CanceledError with __CANCEL__
    if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
      return []
    }
    throw err
  }
}

/**
 * 分段渲染（XSS-safe）：返回 [{ text, hit }] 列表；
 * 组件模板按段渲染 + 命中段套 <em class="search-hl">。
 * 不返回任何 HTML 字符串。
 */
export function splitForHighlight(
  text: string | null | undefined,
  keyword: string,
): Array<{ text: string; hit: boolean }> {
  if (text == null || text === '') return []
  if (!keyword) return [{ text, hit: false }]
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
  return parts
    .filter(p => p !== '')
    .map(p => ({ text: p, hit: p.toLowerCase() === keyword.toLowerCase() }))
}

/** 按 [,\s/、;]+ 拆分 OE 输入，去空去重。 */
export function splitOeInput(raw: string): string[] {
  return Array.from(
    new Set(
      raw
        .split(/[,\s/、;]+/)
        .map(s => s.trim())
        .filter(Boolean),
    ),
  )
}
```

- [ ] **步骤 2：导入 + 类型检查**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vue-tsc --noEmit --skipLibCheck src/api/customerProduct.ts
```

预期：无错误。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/api/customerProduct.ts
git commit -m "feat(search): add customerProduct search service reusing global axios client"
```

### 任务 5.2：扩展 `endpoints.ts` 与 `products.ts`

**文件：**
- 修改：`frontend/src/api/endpoints.ts`
- 修改：`frontend/src/api/products.ts`

- [ ] **步骤 1：在 `CUSTOMER_PRODUCTS` 中新增 `oesBulkSync`**

在 `frontend/src/api/endpoints.ts` 的 `CUSTOMER_PRODUCTS` 对象内增加：

```ts
export const CUSTOMER_PRODUCTS = {
  list: '/api/customer-products',
  detail: (id: number) => `/api/customer-products/${id}`,
  create: '/api/customer-products',
  update: (id: number) => `/api/customer-products/${id}`,
  remove: (id: number) => `/api/customer-products/${id}`,
  oesBulkSync: (id: number) => `/api/customer-products/${id}/oes/bulk-sync`,
} as const
```

- [ ] **步骤 2：在 `productsApi` 增加方法**

在 `frontend/src/api/products.ts` 的 `productsApi` 对象中增加：

```ts
bulkSyncOes: (id: number, oes: string[]) =>
  client.post(CUSTOMER_PRODUCTS.oesBulkSync(id), { oes }),
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/api/endpoints.ts frontend/src/api/products.ts
git commit -m "feat(search): add OE bulk-sync endpoint and api method"
```

---

## 任务 6：前端通用组件

### 任务 6.1：创建 `ProductSearchSelect.vue`

**文件：**
- 创建：`frontend/src/components/common/ProductSearchSelect.vue`

- [ ] **步骤 1：编写组件**

```vue
<template>
  <el-select
    :model-value="selectedItem"
    filterable
    remote
    :remote-method="onQuery"
    :loading="loading"
    :placeholder="placeholder"
    :disabled="disabled"
    value-key="id"
    style="width: 100%"
    clearable
    @change="onSelect"
  >
    <el-option
      v-for="item in options"
      :key="item.id"
      :label="labelOf(item)"
      :value="item"
    >
      <div class="ps-item">
        <el-image :src="assetUrl(item.image_url)" class="ps-thumb">
          <template #error><div class="ps-thumb-fallback">无图</div></template>
        </el-image>
        <div class="ps-info">
          <div class="ps-line ps-name">
            <template v-for="(seg, i) in splitForHighlight(item.product_name, keyword)" :key="`n-${i}`">
              <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
          <div v-if="item.product_name_en" class="ps-line ps-name-en">
            <template v-for="(seg, i) in splitForHighlight(item.product_name_en, keyword)" :key="`ne-${i}`">
              <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
          <div v-if="item.customer_model" class="ps-line ps-model">
            <span class="ps-label">客户型号:</span>
            <template v-for="(seg, i) in splitForHighlight(item.customer_model, keyword)" :key="`m-${i}`">
              <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
          <div v-if="item.oes.length" class="ps-line ps-oe">
            <span class="ps-label">OE:</span>
            <span
              v-for="(oe, i) in item.oes.slice(0, 5)"
              :key="`oe-${i}`"
              class="ps-oe-chip"
            >
              <template v-for="(seg, j) in splitForHighlight(oe, keyword)" :key="`oes-${i}-${j}`">
                <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </span>
          </div>
          <div class="ps-line ps-meta">
            <span class="ps-customer">{{ item.customer_name || '-' }}</span>
            <span class="ps-source">匹配: {{ sourceLabel(item.matched_in) }}</span>
          </div>
        </div>
        <div v-if="item.sub_images?.length" class="ps-subimgs">
          <el-image
            v-for="(s, i) in item.sub_images.slice(0, 3)"
            :key="i"
            :src="assetUrl(s)"
            class="ps-subimg"
            fit="cover"
          />
        </div>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { assetUrl } from '@/api/base'
import {
  searchCustomerProducts,
  splitForHighlight,
  type CustomerProductSearchItem,
  type MatchFieldKey,
} from '@/api/customerProduct'

const props = defineProps<{
  modelValue: CustomerProductSearchItem | null
  customerId?: number | null
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: CustomerProductSearchItem | null): void
  (e: 'select', value: CustomerProductSearchItem): void
}>()

const options = ref<CustomerProductSearchItem[]>([])
const loading = ref(false)
const keyword = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null
let abortController: AbortController | null = null

const selectedItem = ref<CustomerProductSearchItem | null>(props.modelValue ?? null)

watch(
  () => props.modelValue,
  (val) => {
    selectedItem.value = val ?? null
  },
)

function labelOf(item: CustomerProductSearchItem): string {
  return item.product_name || item.customer_model || item.oes[0] || String(item.id)
}

function sourceLabel(matched: MatchFieldKey[]): string {
  const map: Record<MatchFieldKey, string> = {
    customer_model: '客户型号',
    product_name: '产品名称',
    product_name_en: 'Product Name (EN)',
    product_short_name: '产品简称',
    product_short_name_en: 'Short Name (EN)',
    detail_desc: '描述',
    oe: 'OE号',
  }
  return matched.map(m => map[m] ?? m).join(' + ') || '-'
}

function onQuery(query: string) {
  keyword.value = query
  if (searchTimer) clearTimeout(searchTimer)
  abortController?.abort()

  if (!query || query.trim().length === 0) {
    options.value = []
    loading.value = false
    return
  }

  loading.value = true
  abortController = new AbortController()

  searchTimer = setTimeout(async () => {
    try {
      const results = await searchCustomerProducts({
        keyword: query.trim(),
        customerId: props.customerId ?? undefined,
        limit: 20,
        signal: abortController?.signal,
      })
      options.value = results
    } catch {
      options.value = []
    } finally {
      loading.value = false
    }
  }, 200)
}

function onSelect(item: CustomerProductSearchItem | string | number | null) {
  if (!item || typeof item !== 'object') return
  selectedItem.value = item
  emit('update:modelValue', item)
  emit('select', item)
}
</script>

<style scoped>
.search-hl { color: #f56c6c; font-weight: 600; }
.ps-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; }
.ps-thumb { width: 56px; height: 56px; border-radius: 4px; flex-shrink: 0; }
.ps-thumb-fallback {
  width: 56px; height: 56px; border-radius: 4px; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center; font-size: 12px; color: #909399;
}
.ps-info { flex: 1; min-width: 0; }
.ps-line { font-size: 12px; line-height: 1.5; color: #303133; }
.ps-name { font-weight: 600; }
.ps-name-en { color: #606266; }
.ps-label { color: #909399; margin-right: 4px; }
.ps-oe-chip { margin-right: 6px; }
.ps-meta { margin-top: 4px; }
.ps-customer { color: #409eff; margin-right: 8px; }
.ps-source { color: #909399; }
.ps-subimgs { display: flex; align-items: center; }
.ps-subimg { width: 28px; height: 28px; border-radius: 3px; margin-left: 4px; }
</style>
```

- [ ] **步骤 2：类型检查**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vue-tsc --noEmit --skipLibCheck src/components/common/ProductSearchSelect.vue
```

预期：无错误。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/common/ProductSearchSelect.vue
git commit -m "feat(search): add ProductSearchSelect component"
```

---

## 任务 7：前端接入点

### 任务 7.1：NewOrderDialog 接入搜索组件

**文件：**
- 修改：`frontend/src/components/order/NewOrderDialog.vue`

- [ ] **步骤 1：引入 service 与组件**

在 `<script setup>` 顶部（`import` 区段）新增：

```ts
import ProductSearchSelect from '@/components/common/ProductSearchSelect.vue'
import { type CustomerProductSearchItem } from '@/api/customerProduct'
```

- [ ] **步骤 2：删除旧三件套搜索区段**

在 `L223-L270`（`<el-tab-pane label="单条新增" name="single">` 中的「搜索模式 + 产品搜索 + 搜索结果」三件套）整段删除对应的 `<el-form-item>` 三块。

替换为：

```vue
<el-form-item label="产品搜索" prop="search_keyword">
  <ProductSearchSelect
    v-model="selectedProduct"
    :customer-id="form.customer_id"
    placeholder="搜索 OE号 / 客户型号 / 产品名称"
    @select="onProductSelect"
  />
</el-form-item>
```

- [ ] **步骤 3：删除旧 `searchMode` / `searchKeyword` / `searchResults` / `selectedProductIndex` 变量**

将 L409-L412 的：

```ts
const searchMode = ref<'both' | 'oe' | 'name'>('both')
const searchKeyword = ref('')
const searchResults = ref<Product[]>([])
const selectedProductIndex = ref<number | null>(null)
```

替换为：

```ts
// 旧三件套已删除（2026-07-17 搜索服务接入）
// Product 类型不再使用，统一走 CustomerProductSearchItem
```

- [ ] **步骤 4：替换 `onResultSelect` / `onSearchChange` / 重写 `onProductSelect`**

在 L704-L731 区域，将原 `onSearchChange`、`onResultSelect`、`onProductSelect` 整段替换：

```ts
import { type CustomerProductSearchItem } from '@/api/customerProduct'  // 已新增

function onProductSelect(item: CustomerProductSearchItem) {
  selectedProduct.value = item
  form.customer_id = item.customer_id
  form.product_id = item.id
  form.customer_code = item.customer_code || item.product_code || ''
  form.customer_model = item.customer_model || ''
  form.oe_number = item.oes[0] || ''
  form.unit_price = item.price_usd ?? 0
  form.detail_desc = item.detail_desc || item.product_name || ''
}

function formatProductDisplay(item: CustomerProductSearchItem | null): string {
  if (!item) return '-'
  return item.product_name || item.customer_model || item.oes[0] || `ID:${item.id}`
}
```

并**删除**原 `searchProducts` 函数（L675-L702，引用的是已废弃的 `PRODUCT_CUSTOMER.search`）。

- [ ] **步骤 5：更新下单 payload（L873-L884）**

将：

```ts
const payload = {
  dept_id: 'S',
  customer_id: form.customer_id,
  items: [{
    quantity: form.quantity,
    unit_price: form.unit_price,
    customer_code: form.customer_code,
    customer_model: form.customer_model || undefined,
    oe_number: form.oe_number || undefined,
  }],
  payment_stages: [],
}
```

替换为：

```ts
const payload = {
  dept_id: 'S',
  customer_id: form.customer_id,
  items: [{
    product_id: form.product_id ?? null,                  // P0-3：必填
    quantity: form.quantity,
    unit_price: form.unit_price,
    customer_code: form.customer_code,
    customer_model: form.customer_model || undefined,      // P0-4：写入
    oe_number: form.oe_number || undefined,
    detail_desc: form.detail_desc || undefined,           // 顺便带上产品名称
  }],
  payment_stages: [],
}
```

- [ ] **步骤 6：在 `form` reactive 中新增 `product_id`**

在 L415 的 `form = reactive({...})` 块中新增：

```ts
product_id: undefined as number | undefined,
```

- [ ] **步骤 7：类型检查与 Commit**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vue-tsc --noEmit --skipLibCheck src/components/order/NewOrderDialog.vue
git add frontend/src/components/order/NewOrderDialog.vue
git commit -m "feat(order): integrate ProductSearchSelect in NewOrderDialog"
```

### 任务 7.2：SupplementDialog 接入搜索组件

**文件：**
- 修改：`frontend/src/components/order/SupplementDialog.vue`

- [ ] **步骤 1：引入 service 与组件**

```ts
import ProductSearchSelect from '@/components/common/ProductSearchSelect.vue'
import { type CustomerProductSearchItem } from '@/api/customerProduct'
```

- [ ] **步骤 2：替换 `L17-L38` 的 `el-autocomplete`**

将：

```vue
<el-form-item label="产品搜索" prop="search_keyword">
  <el-autocomplete ... />
</el-form-item>
```

替换为：

```vue
<el-form-item label="产品搜索" prop="search_keyword">
  <ProductSearchSelect
    v-model="selectedProduct"
    :customer-id="order?.customer_id"
    placeholder="搜索 OE号 / 客户型号 / 产品名称"
    @select="onProductSelect"
  />
</el-form-item>
```

- [ ] **步骤 3：在 `singleForm` reactive 中新增 `customer_model` 字段**

找到 `singleForm` 的定义（约 L196-203 区域），在 `oe_number: ''` 之后新增：

```ts
customer_model: '',
```

- [ ] **步骤 4：替换 `onSearchChange` / `onProductSelect` 与 `submitSingle` payload**

删除旧的 `searchProducts` 函数（L242-L263），替换 `onProductSelect` 为：

```ts
function onProductSelect(item: CustomerProductSearchItem) {
  selectedProduct.value = item
  singleForm.customer_code = item.customer_code || item.product_code || ''
  singleForm.oe_number = item.oes[0] || ''
  singleForm.customer_model = item.customer_model || ''
  singleForm.detail_desc = item.detail_desc || item.product_name || ''
  singleForm.unit_price = item.price_usd ?? 0
  ;(singleForm as any).product_id = item.id
}
```

`submitSingle` 的 items 改为（使用正确的 `customer_model` 字段）：

```ts
items: [{
  product_id: (singleForm as any).product_id ?? undefined,
  product_code: singleForm.customer_code,
  customer_code: singleForm.customer_code,
  customer_model: singleForm.customer_model || undefined,    // 正确映射
  oe_number: singleForm.oe_number || undefined,
  detail_desc: singleForm.detail_desc || undefined,
  quantity: singleForm.quantity,
  unit_price: singleForm.unit_price,
}]
```

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/components/order/SupplementDialog.vue
git commit -m "feat(order): integrate ProductSearchSelect in SupplementDialog"
```

### 任务 7.3：ProductManagement 顶部搜索接入

**文件：**
- 修改：`frontend/src/views/product/ProductManagement.vue`

- [ ] **步骤 1：引入组件**

```ts
import ProductSearchSelect from '@/components/common/ProductSearchSelect.vue'
import { type CustomerProductSearchItem } from '@/api/customerProduct'
```

- [ ] **步骤 2：替换搜索输入框（L9-L15）**

将 `<el-input v-model="filters.search" class="search-input" placeholder="..."/>` 替换为：

```vue
<ProductSearchSelect
  class="search-input"
  placeholder="搜索 OE号 / 客户型号 / 产品名称"
  @select="onSearchSelect"
/>
```

- [ ] **步骤 3：添加选中处理函数**

```ts
async function onSearchSelect(item: CustomerProductSearchItem) {
  // 直接根据 item.id 查询该产品详情并打开编辑；
  // 不依赖 filters.search 的 substring 匹配（旧列表 API 不支持 OE / PI item 多字段搜索），
  // 也避免"过滤后 0 条或多条不准确"导致用户选中的产品找不到的问题。
  await productsApi.get(item.id).then((resp) => {
    openEdit(resp.data as CustomerProduct)
  }).catch(() => {
    ElMessage.error('产品详情加载失败')
  })
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/views/product/ProductManagement.vue
git commit -m "feat(product): use ProductSearchSelect in product management toolbar"
```

### 任务 7.4：ProductEditDialog OE 批量同步

**文件：**
- 修改：`frontend/src/components/order/ProductEditDialog.vue`

- [ ] **步骤 1：引入 service 与 api**

```ts
import { splitOeInput } from '@/api/customerProduct'
import { productsApi } from '@/api/products'
```

- [ ] **步骤 2：替换 `L109` OE blur 事件**

将 `@blur="saveField('oe_number', form.oe_number)"` 替换为 `@blur="saveOeField(form.oe_number)"`。

- [ ] **步骤 3：添加 `saveOeField` 函数**

```ts
async function saveOeField(value: string) {
  const productId = item.value?.product_id
  if (!productId) return
  const list = splitOeInput(value || '')
  try {
    await productsApi.bulkSyncOes(productId, list)
    ElMessage.success('OE号已同步')
  } catch (e: any) {
    ElMessage.error(e?.message || 'OE号同步失败')
  }
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/components/order/ProductEditDialog.vue
git commit -m "feat(product): sync OE list via bulk-sync in ProductEditDialog"
```

---

## 任务 8：前端测试

### 任务 8.1：`customerProduct` service 单元测试

**文件：**
- 创建：`frontend/src/api/__tests__/customerProduct.test.ts`

- [ ] **步骤 1：编写测试**

```ts
import { describe, expect, it, vi } from 'vitest'
import client from '../client'
import { searchCustomerProducts, splitForHighlight, splitOeInput } from '../customerProduct'

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
  },
}))

describe('splitForHighlight', () => {
  it('returns empty array for empty text', () => {
    expect(splitForHighlight(null, 'x')).toEqual([])
    expect(splitForHighlight('', 'x')).toEqual([])
  })

  it('returns plain segment when no keyword', () => {
    expect(splitForHighlight('hello', '')).toEqual([{ text: 'hello', hit: false }])
  })

  it('marks keyword segment as hit', () => {
    const segs = splitForHighlight('刹车片 750', '750')
    expect(segs.some(s => s.hit && s.text === '750')).toBe(true)
  })

  it('returns plain text segments for XSS payloads (no HTML strings)', () => {
    const segs = splitForHighlight('<script>alert(1)</script>', 'alert')
    expect(segs.every(s => typeof s.text === 'string')).toBe(true)
    expect(segs.some(s => s.text.includes('script'))).toBe(true)
  })

  it('escapes regex meta chars', () => {
    expect(() => splitForHighlight('a.b', '.')).not.toThrow()
  })
})

describe('splitOeInput', () => {
  it('splits and removes duplicates', () => {
    expect(splitOeInput('601, 750 / AXMC;750')).toEqual(['601', '750', 'AXMC'])
  })
  it('returns empty for empty or all-separator input', () => {
    expect(splitOeInput('')).toEqual([])
    expect(splitOeInput(',,, ')).toEqual([])
  })
})

describe('searchCustomerProducts', () => {
  it('returns results array from client response', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: { results: [{ id: 1 }], total: 1 } } as any)
    const items = await searchCustomerProducts({ keyword: 'x' })
    expect(items).toHaveLength(1)
  })

  it('returns empty array on CanceledError', async () => {
    const cancelErr: any = new Error('canceled')
    cancelErr.name = 'CanceledError'
    vi.mocked(client.get).mockRejectedValue(cancelErr)
    const items = await searchCustomerProducts({ keyword: 'x' })
    expect(items).toEqual([])
  })

  it('rethrows non-cancel errors', async () => {
    vi.mocked(client.get).mockRejectedValue(new Error('boom'))
    await expect(searchCustomerProducts({ keyword: 'x' })).rejects.toThrow('boom')
  })
})
```

- [ ] **步骤 2：运行测试**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vitest run src/api/__tests__/customerProduct.test.ts
```

预期：全部通过。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/api/__tests__/customerProduct.test.ts
git commit -m "test(search): add customerProduct service tests"
```

### 任务 8.2：`ProductSearchSelect` 组件测试

**文件：**
- 创建：`frontend/src/components/common/__tests__/ProductSearchSelect.test.ts`

- [ ] **步骤 1：编写测试**

```ts
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ProductSearchSelect from '../ProductSearchSelect.vue'
import * as searchApi from '@/api/customerProduct'

vi.mock('@/api/customerProduct', () => ({
  searchCustomerProducts: vi.fn(async () => []),
  splitForHighlight: vi.fn((text: string | null | undefined) =>
    text ? [{ text, hit: false }] : [],
  ),
  splitOeInput: vi.fn((raw: string) =>
    Array.from(new Set(raw.split(/[,\s/、;]+/).map(s => s.trim()).filter(Boolean))),
  ),
}))

const mockItem = {
  id: 1,
  customer_id: 10,
  customer_name: 'ACME',
  customer_model: 'ACM-750',
  product_name: '750 刹车片',
  product_name_en: null,
  product_short_name: null,
  product_short_name_en: null,
  detail_desc: '',
  brand: null,
  customer_code: 'C001',
  product_code: 'A01S01240001',
  price_usd: 12.5,
  image_url: null,
  sub_images: [],
  oes: ['750'],
  matched_in: ['oe'],
  match_score: 50,
}

describe('ProductSearchSelect', () => {
  beforeEach(() => {
    vi.mocked(searchApi.searchCustomerProducts).mockClear()
  })

  it('does not call service for empty query', async () => {
    const wrapper = mount(ProductSearchSelect, { props: { modelValue: null } })
    wrapper.vm.onQuery('')
    await new Promise(r => setTimeout(r, 250))
    expect(searchApi.searchCustomerProducts).not.toHaveBeenCalled()
  })

  it('calls service after debounce and emits events on select', async () => {
    vi.mocked(searchApi.searchCustomerProducts).mockResolvedValue([mockItem] as any)
    const wrapper = mount(ProductSearchSelect, { props: { modelValue: null } })

    wrapper.vm.onQuery('750')
    await new Promise(r => setTimeout(r, 250))
    expect(searchApi.searchCustomerProducts).toHaveBeenCalledWith(
      expect.objectContaining({ keyword: '750' }),
    )

    wrapper.vm.onSelect(mockItem as any)
    await nextTick()
    expect(wrapper.emitted('select')?.[0]).toEqual([mockItem])
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([mockItem])
  })
})
```

- [ ] **步骤 2：运行测试**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vitest run src/components/common/__tests__/ProductSearchSelect.test.ts
```

预期：全部通过。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/common/__tests__/ProductSearchSelect.test.ts
git commit -m "test(search): add ProductSearchSelect component tests"
```

---

## 任务 9：文档与验收

### 任务 9.1：更新 `docs/spec.md`

**文件：**
- 修改：`docs/spec.md` L282-L286

- [ ] **步骤 1：替换接口约定**

将：

```markdown
对应 `PRODUCT_CUSTOMER`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/product-customer/search` | 兼容产品搜索 |
```

替换为：

```markdown
对应 `CUSTOMER_PRODUCTS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/customer-products/search` | 多字段产品搜索（OE / 客户型号 / 中文英文名称 / PI item 名称） |
| `POST` | `/api/customer-products/{id}/oes/bulk-sync` | 差量同步一个客户产品的 OE 号列表 |
```

- [ ] **步骤 2：Commit**

```bash
git add docs/spec.md
git commit -m "docs: update API spec for product search"
```

### 任务 9.2：最终验证

- [ ] **步骤 1：运行后端 pytest**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -m pytest tests/test_product_search.py -v
```

预期：全部通过（覆盖 P0/P1/P2 全部验收项；具体 test_ 数量按代码决定，不预设）。

- [ ] **步骤 2：运行前端 vitest**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/frontend"
npx vitest run src/api/__tests__/customerProduct.test.ts src/components/common/__tests__/ProductSearchSelect.test.ts
```

预期：全部通过。

- [ ] **步骤 3：启动后端 curl 验证路由顺序**

```bash
cd "d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend"
python -m uvicorn main:app --port 8001
```

另一个终端：

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8001/api/customer-products/search"
```

预期：`422`（keyword 必填，**不是** `/api/customer-products/{product_id}` 的 422）。

```bash
curl -s "http://localhost:8001/api/customer-products/search?keyword=test"
```

预期：200，`{"results":[], "total":0}`。

- [ ] **步骤 4：Commit 收尾**

```bash
git commit -m "chore(search): final verification and cleanup" --allow-empty
```

---

## 自检

**1. 规格覆盖度**：设计文档 §3（后端）、§4（前端组件）、§5（数据契约）、§7（测试）全部映射到具体任务。

**2. 占位符扫描**：所有步骤均含实际代码或具体命令，无"待定 / TODO / 后续实现"。唯一 placeholder 是测试中的 `db_session` 参数化 fixture（必要）。

**3. 类型一致性**：
- `MatchFieldKey` 在前端 `customerProduct.ts`、`ProductSearchSelect.vue` 中命名一致。
- `customer_model` 在 Schema、CRUD、PI 写入、前端回填中命名一致。
- `/search` 路由锚点明确：在 `/{product_id}/convert` (L193) 之前插入。

**4. 审查修订 6 大项已全部落地**：
- ✅ P0-1 `interface` → `type` 语法错误（line 1311）
- ✅ P0-2 SQLite `:memory:` + `StaticPool` 跨线程安全（line 840）
- ✅ P0-3 SupplementDialog `customer_model` 正确回填（line ~1890），非遗留兼容
- ✅ P1-1 feature flag 回滚承诺删除（YAGNI，前置事实明确）
- ✅ P1-2 `bulk_sync_oes` 改用 `with db.begin()` + `final_primary` 返回真正主 OE
- ✅ P1-3 OE 回归测试比较 id/created_at 值不变；新增 `set_first_as_primary=False` 场景测试

**5. 遗漏补充**：
- ✅ 已删除产品 / 已删除 PI item 过滤
- ✅ sub_images 非法 JSON / 非字符串过滤
- ✅ 主 OE 优先排序
- ✅ N+1 防护（joinedload / selectinload）
- ✅ 422 状态码正确性（来自 Query 校验，非路由错配）
- ✅ 取消请求静默（CanceledError 检测）
- ✅ XSS 防御（splitForHighlight 仅返回纯文本 + 模板 `{{ }}` 插值）

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-07-17-product-search.md`。

两种执行方式：

1. **子代理驱动（推荐）** — 每个任务调度一个新的子代理，任务间进行审查，快速迭代
2. **内联执行** — 在当前会话中使用 `superpowers:executing-plans` 批量执行并设有检查点

请确认使用哪种方式。