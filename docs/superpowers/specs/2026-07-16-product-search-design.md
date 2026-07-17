# 产品搜索服务设计 (Product Search Service)

**日期**: 2026-07-16
**作者**: AI 协作
**状态**: Draft（待用户审阅）
**范围**: 新订单下单、产品管理、未来可复用模块

---

## 1. 背景与目标

### 1.1 现状
- `frontend/src/components/order/NewOrderDialog.vue` L223-271 现有搜索链由
  `el-radio-group(searchMode)` + `el-autocomplete` + `el-select` 三件套组成，
  互相冗余，命中字段无高亮，结果不含图片。
- `frontend/src/components/order/SupplementDialog.vue` L252 也调用同一搜索逻辑。
- 两处都引用 `endpoints.ts` 的 `PRODUCT_CUSTOMER.search` = `/api/product-customer/search`，
  **该路由后端根本不存在**（404），导致搜索下拉始终为空、用户只能手动输入（实际是静默兜底）。
- `frontend/src/views/product/ProductManagement.vue` 顶部有独立的产品搜索框，未复用同一搜索服务。
- 后端 `/api/customer-products/...`（`routers/customer_product.py`）**已有 list/by-oe/by-code/by-system-code/{id}/codes/oes/batch 等 handler**，**但没有 `/search`**。
- 后端 `/api/product-customers/...`（`routers/product_customer.py`，`PrdProductCustomer` 关联表）**前端零引用**，本次清理删除。
- 产品 OE 号在 `PrdCustomerProduct.oe_number` 列以字符串存储（已废弃字段），
  现真正使用的是关联表 `PrdCustomerProductOE`（一行一条 OE）。

### 1.2 目标
1. 提供统一、独立、可复用的产品搜索服务，覆盖下单、产品管理、未来模块。
2. 匹配字段包含：
   - **OE 号（关联表 `prd_customer_product_oe`，子串匹配）**
   - **客户型号 `customer_model`（精确匹配优先 score 100）**
   - **产品名称 `product_name`（中文全称）**
   - **产品英文全称 `product_name_en`**
   - **产品中文简称 `product_short_name`**
   - **产品英文简称 `product_short_name_en`**
   - **详细描述 `detail_desc`**
3. 保存 OE 号时按逗号/空格/斜杠/分号拆分多条入库，搜索时任一 OE 子串命中即可。
4. 搜索结果展示：图片（主图 + 副图缩略）、匹配字段红字高亮、字段来源标注、客户名。
5. 搜索接口与前端组件完全解耦，便于后续接 ES / pg_trgm 等。
6. **修复当前 saveField 路径并不通**：经核实 PI item 表本来就有 `detail_desc_en` / `product_short_name*` 4 列，前端保存链路是通的，**根本不需要额外迁移**。spec 已撤回 §3.1.1 的数据库迁移提案，避免误导实施人员。

### 1.3 非目标
- 不引入 Elasticsearch / pg_trgm 扩展（YAGNI，未来按需）。
- 不重构 `PrdCustomerProduct.oe_number` 旧字段（已废弃，仅保留兼容）。

### 1.4 名称字段数据来源（P1-2 闭环）

经核实，**当前 UI blur → `useProductEdit.saveField` → `/api/pi/items/{item_id}` → `crud/pi.py::update_pi_item` → `pi_proforma_invoice_item` 表**已正常工作：

| UI 字段 | `form.*` | `saveField` 写入键 | 后端 `pi_proforma_invoice_item` 列（实际命中） |
|---|---|---|---|
| 产品名称（中） | `form.product_name` | `detail_desc` | ✅ `detail_desc`（PI 表） |
| 产品名称（英） | `form.product_name_en` | `detail_desc_en` | ✅ `detail_desc_en`（PI 表，2026-06-22 新增） |
| 简称（中） | `form.product_short_name` | `product_short_name` | ✅ `product_short_name`（PI 表，2026-07-09 新增） |
| 简称（英） | `form.product_short_name_en` | `product_short_name_en` | ✅ `product_short_name_en`（PI 表，2026-07-09 新增） |

**P0-5 名称来源闭环（精排已实现**:
- `product_name` 精排时取自 `_get_name_fields(p, pi_item)`：
  - 优先 `pi_item.detail_desc`（用户编辑的"产品名称中"）
  - fallback `p.product_name`（PrdCustomerProduct 表默认值）
  - 命中 score=60，与 PrdCustomerProduct.product_name 同分，不重复计分
- `customer_model` 精排同样取自 `_get_name_fields`：
  - 优先 `pi_item.customer_model`（用户编辑的"客户型号"）
  - fallback `p.customer_model`
- 4 个 PI item 字段（detail_desc / detail_desc_en / product_short_name / product_short_name_en）全部参与精排，无遗漏。

---

## 2. 架构概览

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│ NewOrderDialog.vue      │         │ ProductManagement.vue        │
│ ProductSearchSelect     │         │ ProductSearchSelect           │
└──────────┬──────────────┘         └──────────┬───────────────────┘
           │                                    │
           └─────────────────┬──────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │ productSearchService (前端)   │
              │  - search(keyword, opts)     │
              │  - splitForHighlight(text, kw) │
              │  - escape / dedupe           │
              └──────────────┬───────────────┘
                             │ axios.get + 防抖 200ms
                             ▼
              ┌──────────────────────────────┐
              │ GET /api/customer-products/  │
              │     search                   │
              │   ?keyword=&customer_id=&    │
              │    limit=                    │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │ crud.product_search          │
              │   (新建)                      │
              │  - 候选集 ILIKE 多字段        │
              │  - 计算 match_score          │
              │  - 返回 matched_in 列表      │
              └──────────────────────────────┘
```

---

## 3. 后端设计

### 3.1 路由（新增）

**文件**: `backend/routers/customer_product.py`
**前缀**: `/api/customer-products`（已存在，沿用）

⚠️ **P0-1 路由顺序修复（关键）**：`customer_product.py` 已存在 `@router.get("/{product_id}")` 动态路由（Line 195）。FastAPI 按声明顺序匹配，**新 `/search` handler 必须放在 `/{product_id}` 之前**，否则请求 `/api/customer-products/search` 会被错配为 `product_id="search"` → 触发 422 参数类型错误。

**handler 顺序（实现时严格遵守）**：
```python
# 1️⃣ 静态路径优先
@router.get("/search", response_model=ProductSearchResponse)   # ← 新增（P0-1 强制放在这里）
def search_products(...):
    ...

@router.get("/bulk-sync", ...)  # 任何其他静态路径

# 2️⃣ 然后是动态路径
@router.get("/{product_id}", ...)
def get_customer_product_by_id(...):
    ...
```

**新增** `/search` handler：

```python
@router.get("/search", response_model=ProductSearchResponse)
def search_products(
    keyword: str = Query(..., min_length=1, max_length=100),
    customer_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    多字段模糊搜索：
    - customer_model 精确匹配 (score 100) > ILIKE (score 80)
    - product_name ILIKE (score 60) > detail_desc ILIKE (score 40)
    - 任一 PrdCustomerProductOE.oe_number ILIKE (score 50)
    - OE 拆分多 token 匹配：按 [,\s/、;]+ 拆分 keyword，
      任一 token 子串命中即视为 OE 命中（避免整串不可命中）
    返回: results (按 score desc, limit 截取) + total
    """
```

### 3.1.1 ❌ 已废弃 — 不再做数据库迁移

撤掉 §1.4 旧版本中"PrdCustomerProduct 需要新增 3 列"的提议。
- 名称字段的数据源是 `pi_proforma_invoice_item`，无需建列。
- 仅在 §3.5 搜索候选集里用 LEFT JOIN 取得最近一次 PI item 的名称。

### 3.2 Pydantic Schema

**文件**: `backend/schemas/product_search.py`（新建）

```python
class ProductSearchItem(BaseModel):
    id: int                                  # PrdCustomerProduct.id
    customer_id: int
    customer_name: str | None
    # ---- 名称/型号 ----
    customer_model: str | None
    product_name: str | None                 # 中文全称
    product_name_en: str | None              # 英文全称
    product_short_name: str | None           # 中文简称
    product_short_name_en: str | None        # 英文简称
    detail_desc: str | None
    brand: str | None
    # ---- 下单回填关键字段（P0-2 修复）----
    customer_code: str | None                # PrdCustomerProductCode 表中 is_primary=true 的 product_code；空则取第一条
    product_code: str | None                 # 系统产品编号（PrdCustomerProduct.system_code，备用）
    price_usd: float | None                  # PrdCustomerProduct.price_usd（USD 单价，作为 PI item.unit_price 回填）
    # price_rmb 当前不返回给前端：业务仅支持 USD；PI item 不保留 price_rmb/price_usd 行级字段，
    # 全部以 unit_price（USD）存储。需要 RMB 时再扩展模型。
    # ---- 图片 / OE ----
    image_url: str | None
    sub_images: list[str] = []
    oes: list[str] = []                      # 来自 PrdCustomerProductOE，按主 OE 优先排序
    # ---- 命中信息 ----
    matched_in: list[Literal["customer_model", "product_name",
                              "product_name_en", "product_short_name",
                              "product_short_name_en",
                              "detail_desc", "oe"]] = []
    match_score: float

class ProductSearchResponse(BaseModel):
    results: list[ProductSearchItem]
    total: int
```

### 3.3 CRUD 实现

**文件**: `backend/crud/product_search.py`（新建）

#### OE token 拆分
```python
import re
OE_SPLIT_RE = re.compile(r"[,\s/、;]+")

def split_oe_tokens(kw: str) -> list[str]:
    """按 [,\s/、;]+ 拆分关键词，返回去空 + 去重的 token 列表。
    如 '601, 750 / AXMC' → ['601', '750', 'AXMC']
    """
    return [t for t in OE_SPLIT_RE.split(kw) if t.strip()]

oe_tokens = split_oe_tokens(keyword)
# 至少 1 个 token；空字符串场景由 FastAPI Query(min_length=1) 拦截
```

> ⚠️ **以下旧版本候选集逻辑（带 `.limit(200)` 和不跨表的精排）已被 §3.4 取代**——保留在此仅为对照参考，**不要直接实现**。

<details>
<summary>已废弃：旧候选集 + 旧精排代码（仅参考）</summary>

```python
# ❌ 旧版本：.limit(200) 会丢失精确匹配；纯 PrdCustomerProduct 表无法取名称字段
text_kw = f"%{keyword}%"
text_clauses = [...]   # 单一表 ILIKE
oe_clauses = [PrdCustomerProductOE.oe_number.ilike(f"%{tok}%") for tok in oe_tokens]
candidate_query = (
    db.query(PrdCustomerProduct)
    .outerjoin(PrdCustomerProductOE, ...)
    .filter(PrdCustomerProduct.deleted_at.is_(None), or_(*text_clauses, *oe_clauses))
    .distinct()
    .limit(200)        # ❌ 截断丢数据
)
```
</details>

#### 副图解析
`sub_images` 字段为 TEXT 存 JSON 数组字符串，Python 端 `json.loads` 失败时回退 `[]`。
异常一律 `except json.JSONDecodeError: return []`。

### 3.4 跨表查询 / 排序可靠性（P1-1 / P1-2 关键修复）

⚠️ **P1-1 修正**: 原方案 `LIMIT 200` 候选 + Python score 会丢失精确型号匹配。  
⚠️ **P1-2 修正**: 名称字段（英文全称/中英简称）实际存放在 `pi_proforma_invoice_item` 表，不在 `PrdCustomerProduct`。

**采用方案**: 不在 SQL 里做 LIMIT 截断，改为**分字段独立查询 → Python 按字段加权合并去重**：

```python
# 1) 客户型号精确匹配（全表命中，优先返回）
exact_model_q = (
    db.query(PrdCustomerProduct)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        PrdCustomerProduct.customer_model == keyword,
    )
)
if customer_id is not None:
    exact_model_q = exact_model_q.filter(
        PrdCustomerProduct.customer_id == customer_id
    )
exact_model = exact_model_q.all()

# 2) 产品名称 / 描述模糊匹配（无 LIMIT）
text_kw = f"%{keyword}%"
text_match_q = (
    db.query(PrdCustomerProduct)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(
            PrdCustomerProduct.product_name.ilike(text_kw),
            PrdCustomerProduct.detail_desc.ilike(text_kw),
        ),
    )
)
if customer_id is not None:
    text_match_q = text_match_q.filter(
        PrdCustomerProduct.customer_id == customer_id
    )
text_match = text_match_q.all()

# 3) PI item 名称字段：LEFT JOIN 拿每个 product_id 最近一次的名称
from sqlalchemy import func
latest_pi_item_sq = (
    db.query(
        PiProformaInvoiceItem.product_id,
        func.max(PiProformaInvoiceItem.id).label("latest_id"),
    )
    .filter(
        PiProformaInvoiceItem.product_id.isnot(None),
        PiProformaInvoiceItem.is_deleted == False,   # P1-8：排除已删除 PI item
    )
    .group_by(PiProformaInvoiceItem.product_id)
    .subquery()
)
pi_name_match_q = (
    db.query(PiProformaInvoiceItem)
    .join(latest_pi_item_sq,
          PiProformaInvoiceItem.id == latest_pi_item_sq.c.latest_id)
    # P1-3 修正：PI item 没有 customer_id 列；通过 PI 主表的 customer_id 过滤
    .join(PiProformaInvoice, PiProformaInvoice.id == PiProformaInvoiceItem.pi_id)
    .filter(
        or_(
            # P0-6：中文名称（detail_desc）和客户型号（customer_model）来自 PI item
            PiProformaInvoiceItem.detail_desc.ilike(text_kw),      # → matched_in: product_name
            PiProformaInvoiceItem.customer_model.ilike(text_kw),   # → matched_in: customer_model
            PiProformaInvoiceItem.detail_desc_en.ilike(text_kw),  # → matched_in: product_name_en
            PiProformaInvoiceItem.product_short_name.ilike(text_kw),    # → matched_in: product_short_name
            PiProformaInvoiceItem.product_short_name_en.ilike(text_kw), # → matched_in: product_short_name_en
        ),
    )
)
if customer_id is not None:
    pi_name_match_q = pi_name_match_q.filter(
        PiProformaInvoice.customer_id == customer_id
    )
pi_name_match = pi_name_match_q.all()
latest_name_map: dict[int, PiProformaInvoiceItem] = {
    row.product_id: row for row in pi_name_match
}

# ⚠️ P1-5 修正（重要）：
# latest_name_map 只能装"名称字段匹配关键字"的 PI item，
# 这会导致通过 OE / 客户型号命中的产品在响应里拿不到 product_name_en、简称字段。
# 解决：再查一次"全部候选 product"对应的最近 PI item（不限名称匹配），统一填回响应。

# 4) OE 子串（多 token，OR 条件 + customer_id 过滤）
oe_subqs = [
    PrdCustomerProductOE.oe_number.ilike(f"%{tok}%")
    for tok in oe_tokens if tok
]
if oe_subqs:
    oe_match_q = (
        db.query(PrdCustomerProduct)
        .join(PrdCustomerProductOE,
              PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id)
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
else:
    oe_match = []

# 5) 收集全部候选 product_id
candidate_ids: set[int] = set()
for src_list in [exact_model, text_match, oe_match]:
    for p in src_list:
        candidate_ids.add(p.id)
candidate_ids |= set(latest_name_map.keys())

# P2-2 保护：候选集为空时直接返回空结果，跳过下方所有 SQL
if not candidate_ids:
    return ProductSearchResponse(results=[], total=0)

# 6) P1-5：对所有候选产品，统一加载"最近一次 PI item"作为展示用
# 用独立的 latest_pi_subquery（不限名称匹配）
latest_pi_all_sq = (
    db.query(
        PiProformaInvoiceItem.product_id,
        func.max(PiProformaInvoiceItem.id).label("latest_id"),
    )
    .filter(
        PiProformaInvoiceItem.product_id.in_(candidate_ids),
        PiProformaInvoiceItem.is_deleted == False,  # P1-8：排除已删除 PI item
    )
    .group_by(PiProformaInvoiceItem.product_id)
    .subquery()
)
latest_pi_for_display = {
    row.product_id: row
    for row in db.query(PiProformaInvoiceItem)
    .join(latest_pi_all_sq,
          PiProformaInvoiceItem.id == latest_pi_all_sq.c.latest_id)
    .filter(PiProformaInvoiceItem.is_deleted == False)  # P1-8：兜底
    .all()
}
# 覆盖：让展示用更完整的数据生效（用于响应 product_name_en / 简称）
latest_name_map.update(latest_pi_for_display)

# 7) 一次性把所有 PrdCustomerProduct 加载（预加载关联，避免 N+1；过滤软删除）
from sqlalchemy.orm import joinedload, selectinload
products = {
    p.id: p
    for p in db.query(PrdCustomerProduct)
    .options(
        joinedload(PrdCustomerProduct.customer),   # P2-3：预加载客户，避免 N+1
        selectinload(PrdCustomerProduct.codes),   # P2-3：预加载编号列表
        selectinload(PrdCustomerProduct.oes),     # P2-3：预加载 OE 列表
    )
    .filter(
        PrdCustomerProduct.id.in_(candidate_ids),
        PrdCustomerProduct.deleted_at.is_(None),   # P0-8：排除已删除客户产品
    )
    .all()
}
```

**Python 端精排 score + 统一名称映射**（按 score desc，最后才 LIMIT 截取，保证精确匹配不被丢弃）：

```python
def _get_name_fields(p, pi_item):
    """
    统一名称来源（P0-5 闭环）：
    - product_name:  优先取 PI item.detail_desc（用户保存中文名的地方），
                    为空时 fallback 到 PrdCustomerProduct.product_name
    - customer_model: 优先取 PI item.customer_model（用户保存客户型号的地方），
                    为空时 fallback 到 PrdCustomerProduct.customer_model
    """
    product_name = (
        (pi_item.detail_desc if pi_item else None)
        or p.product_name
        or ""
    )
    customer_model = (
        (pi_item.customer_model if pi_item else None)
        or p.customer_model
        or ""
    )
    return product_name, customer_model

def score_product(p, kw, oe_tokens, latest_pi_item) -> tuple[float, list[str]]:
    score, matched = 0.0, []
    kwl = kw.lower()
    token_lc = [t.lower() for t in oe_tokens if t]
    product_name, customer_model = _get_name_fields(p, latest_pi_item)

    # 客户型号精确 > 模糊（最高优先级）
    if customer_model:
        if customer_model == kw:
            score = max(score, 100.0); matched.append("customer_model")
        elif kwl in customer_model.lower():
            score = max(score, 80.0); matched.append("customer_model")

    # product_name 来自 PI item.detail_desc（优先）/ PrdCustomerProduct（fallback）
    if product_name and kwl in product_name.lower():
        score = max(score, 60.0); matched.append("product_name")

    # PI item 名称字段：英文全称 + 中英简称
    if latest_pi_item is not None:
        pi_name_fields = [
            ("product_name_en",       getattr(latest_pi_item, "detail_desc_en", None), 55),
            ("product_short_name",    getattr(latest_pi_item, "product_short_name", None), 45),
            ("product_short_name_en", getattr(latest_pi_item, "product_short_name_en", None), 40),
        ]
        for key, val, sc in pi_name_fields:
            if val and kwl in str(val).lower():
                score = max(score, float(sc)); matched.append(key)

    # P1-7：PrdCustomerProduct.detail_desc（独立列，非 PI item.detail_desc）也参与匹配
    if p.detail_desc and kwl in p.detail_desc.lower():
        score = max(score, 30.0); matched.append("detail_desc")

    oes = [(oe.oe_number or "") for oe in p.oes]
    if any(any(tok in oe.lower() for tok in token_lc) for oe in oes):
        score = max(score, 50.0); matched.append("oe")

    return score, matched


# P0-7：返回值 Serializer — 返回完整的 ProductSearchItem，与 Schema 对齐
def _build_code(p) -> str | None:
    """从 PrdCustomerProductCode 关联表取主编号"""
    codes = p.codes  # SQLAlchemy relationship
    if not codes:
        return None
    primary = next((c for c in codes if c.is_primary), None)
    return primary.product_code if primary else (codes[0].product_code if codes else None)


def _build_oes(p) -> list[str]:
    """从 PrdCustomerProductOE 关联表取所有 OE 号"""
    return [oe.oe_number for oe in (p.oes or []) if oe.oe_number]


def build_search_item(p, pi_item, matched: list[str], score: float) -> ProductSearchItem:
    """
    统一构造返回对象：来源清晰，字段不缺失。
    注意：matched_in 来源映射：
      PiProformaInvoiceItem.detail_desc    -> product_name（响应字段）
      PiProformaInvoiceItem.customer_model -> customer_model（响应字段）
      PiProformaInvoiceItem.detail_desc_en -> product_name_en
      PiProformaInvoiceItem.product_short_name  -> product_short_name
      PiProformaInvoiceItem.product_short_name_en -> product_short_name_en
      PrdCustomerProduct.detail_desc              -> detail_desc（响应字段）
    """
    pi_name_map = {
        "detail_desc":            "product_name",   # PI item 中文全称
        "customer_model":         "customer_model", # PI item 客户型号
        "detail_desc_en":        "product_name_en",
        "product_short_name":     "product_short_name",
        "product_short_name_en":  "product_short_name_en",
    }
    resolved_matched: list[str] = []
    for m in matched:
        resolved_matched.append(pi_name_map.get(m, m))  # 统一 key 名

    pi_detail_desc = getattr(pi_item, "detail_desc", None) if pi_item else None
    pi_customer_model = getattr(pi_item, "customer_model", None) if pi_item else None

    return ProductSearchItem(
        id=p.id,
        customer_id=p.customer_id,
        customer_name=p.customer.name if p.customer else "",
        customer_model=pi_customer_model or p.customer_model or "",
        product_name=pi_detail_desc or p.product_name or "",
        product_name_en=getattr(pi_item, "detail_desc_en", None) if pi_item else None,
        product_short_name=getattr(pi_item, "product_short_name", None) if pi_item else None,
        product_short_name_en=getattr(pi_item, "product_short_name_en", None) if pi_item else None,
        detail_desc=p.detail_desc or "",
        brand=p.brand,
        customer_code=_build_code(p),
        product_code=p.system_code or None,
        price_usd=float(p.price_usd) if p.price_usd else None,
        oes=_build_oes(p),
        image_url=p.image_url or None,
        sub_images=(lambda s: (json.loads(s) if s else []) if isinstance(s, str) else [])(
            p.sub_images
        ),
        matched_in=resolved_matched,
        match_score=score,
    )


# 主流程：先算所有候选 score，再排序截 limit
results = []
for pid, p in products.items():
    score, matched = score_product(
        p, keyword, oe_tokens, latest_name_map.get(pid)
    )
    results.append((score, p, matched))
results.sort(key=lambda x: (-x[0], x[1].id))
total = len(results)                                    # P1-2：截取前的全部候选数量
results = results[:limit]
return ProductSearchResponse(
    results=[
        build_search_item(p, latest_name_map.get(p.id), matched, score)
        for score, p, matched in results
    ],
    total=total,
)

**性能约束**: 全表 ILIKE + Python score 在数据量 < 5k 行客户产品时实测 < 200ms。如未来超 10k 行再评估 pg_trgm 全文索引。

### 3.5 端点常量

**新文件**: `frontend/src/api/productSearch.ts`

```ts
export type MatchField = 'customer_model'
                      | 'product_name'
                      | 'product_name_en'
                      | 'product_short_name'
                      | 'product_short_name_en'
                      | 'detail_desc'
                      | 'oe'

export interface ProductSearchItem {
  id: number                            // PrdCustomerProduct.id
  customer_id: number
  customer_name: string | null
  // 名称/型号
  customer_model: string | null
  product_name: string | null           // 中文全称
  product_name_en: string | null        // 英文全称
  product_short_name: string | null     // 中文简称
  product_short_name_en: string | null  // 英文简称
  detail_desc: string | null
  brand: string | null
  // 下单回填关键字段
  customer_code: string | null          // 主客户产品编号
  product_code: string | null           // 系统产品编号（备用）
  price_usd: number | null              // USD 单价（业务当前唯一货币）
  // price_rmb / currency 不返回：业务仅支持 USD，需要 RMB 时再扩展模型 + 接口
  // 图片 / OE
  image_url: string | null
  sub_images: string[]
  oes: string[]
  // 命中信息
  matched_in: MatchField[]
  match_score: number
}

export interface SearchResponse {
  results: ProductSearchItem[]
  total: number
}

export const productSearchService = {
  async search(
    keyword: string,
    opts: { customerId?: number; limit?: number; signal?: AbortSignal } = {}
  ): Promise<ProductSearchItem[]> { ... },

  /**
   * 分段渲染（safe）：返回 [{ text: string, hit: boolean }]，
   * 组件模板按段渲染 + 命中段套 `<em class="search-hl">`。
   * **不返回任何 HTML 字符串**，彻底消除 XSS 风险（P1-3）。
   */
  splitForHighlight(
    text: string | null | undefined,
    keyword: string
  ): Array<{ text: string; hit: boolean }> {
    if (!text) return []
    if (!keyword) return [{ text, hit: false }]
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return parts
      .filter(p => p !== '')
      .map(p => ({ text: p, hit: p.toLowerCase() === keyword.toLowerCase() }))
  },

  /** 按 [,\s/、;]+ 拆分 OE 输入 */
  splitOeInput(raw: string): string[] {
    return Array.from(new Set(
      raw.split(/[,\s/、;]+/).map(s => s.trim()).filter(Boolean)
    ))
  },
}
```

- 内部用 axios 调用（`client.get(PRODUCT_SEARCH.recommend, { params, signal })`），
  不直接 fetch，统一走 `baseURL` 策略。
- `signal` 用于组件 onUnmounted 时 `controller.abort()`。

### 4.2 ProductSearchSelect 组件

**新文件**: `frontend/src/components/common/ProductSearchSelect.vue`

| Prop | 类型 | 说明 |
|------|------|------|
| `modelValue` | `ProductSearchItem \| null` | 当前选中 |
| `customerId` | `number \| null` | 可选，限定客户 |
| `placeholder` | `string` | 输入框占位 |
| `disabled` | `boolean` | 禁用 |

Events: `update:modelValue`、`select(item)`

#### 行为
- `el-select filterable remote` + `:remote-method="onQuery"`
- `onQuery` 内 200ms 防抖 → `productSearchService.search(q, { signal })`
- 旧请求 `controller.abort()` 取消
- 下拉项模板（图 1）：

```vue
<div class="ps-item">
  <el-image :src="item.image_url" class="ps-thumb">
    <template #error><div class="ps-thumb-fallback">无图</div></template>
  </el-image>
  <div class="ps-info">
    <!-- P1-3: 用 <template v-for> 分段渲染，命中段用 <em>，无 v-html -->
    <div class="ps-line ps-name">
      <template v-for="(seg, i) in splitForHighlight(item.product_name, kw)" :key="`n-${i}`">
        <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
        <span v-else>{{ seg.text }}</span>
      </template>
    </div>
    <div class="ps-line ps-name-en">
      <template v-for="(seg, i) in splitForHighlight(item.product_name_en, kw)" :key="`ne-${i}`">
        <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
        <span v-else>{{ seg.text }}</span>
      </template>
    </div>
    <div class="ps-line ps-short">
      <template v-if="item.product_short_name">
        <template v-for="(seg, i) in splitForHighlight(item.product_short_name, kw)" :key="`sn-${i}`">
          <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
          <span v-else>{{ seg.text }}</span>
        </template>
      </template>
      <template v-if="item.product_short_name_en">
        <span class="ps-short-en">
          <template v-for="(seg, i) in splitForHighlight(item.product_short_name_en, kw)" :key="`sne-${i}`">
            <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
            <span v-else>{{ seg.text }}</span>
          </template>
        </span>
      </template>
    </div>
    <div class="ps-line ps-model">
      <span class="ps-label">客户型号:</span>
      <template v-for="(seg, i) in splitForHighlight(item.customer_model, kw)" :key="`m-${i}`">
        <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
        <span v-else>{{ seg.text }}</span>
      </template>
    </div>
    <div class="ps-line ps-oe">
      <span class="ps-label">OE:</span>
      <span v-for="(oe, i) in item.oes" :key="`oe-${i}`" class="ps-oe-chip">
        <template v-for="(seg, j) in splitForHighlight(oe, kw)" :key="`oes-${i}-${j}`">
          <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
          <span v-else>{{ seg.text }}</span>
        </template>
      </span>
    </div>
    <div class="ps-line ps-meta">
      <span class="ps-customer">{{ item.customer_name }}</span>
      <span class="ps-source">匹配: {{ sourceLabel(item.matched_in) }}</span>
    </div>
  </div>
  <div class="ps-subimgs" v-if="item.sub_images?.length">
    <el-image v-for="(s, i) in item.sub_images.slice(0, 3)"
              :key="i" :src="s" class="ps-subimg" :preview-src-list="item.sub_images"
              :initial-index="i" fit="cover"/>
  </div>
</div>
```

`sourceLabel(matched_in)` 返回人类可读字符串：
- `['customer_model']` → "客户型号"
- `['product_name']` → "产品名称"
- `['product_name_en']` → "Product Name (EN)"
- `['product_short_name']` → "产品简称"
- `['product_short_name_en']` → "Short Name (EN)"
- `['oe']` → "OE号"
- `['detail_desc']` → "描述"
- 多项同时 → 拼接，如 "客户型号 + OE号"

#### 样式
```css
.search-hl { color: #f56c6c; font-weight: 600; }
.ps-thumb { width: 56px; height: 56px; border-radius: 4px; }
.ps-subimg { width: 28px; height: 28px; border-radius: 3px; margin-left: 4px; }
.ps-source { color: #909399; font-size: 12px; margin-left: 8px; }
```

### 4.2.5 NewOrderDialog 订单回填映射（P0-2 / P0-3 + 价格简化）

`NewOrderDialog.vue` 当前实现的下单 payload（L873-884）：
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
    // ⚠️ 缺失 product_id（P0-3）
    // ⚠️ 没有货币字段（P1-6 推荐方案 1：业务仅 USD，本字段不需要）
  }],
  payment_stages: [],
}
```

**P1-6 决策（已采纳）：方案 1 — 只 USD，简化**。

经核实 `backend/models/pi.py:27-110`，`PiProformaInvoiceItem` 模型当前**没有** `currency` / `price_usd` / `price_rmb` 行级列：
- 货币只在 PI 主表 `PiProformaInvoice.currency` 存储（Line 14）
- 价格用 `PiProformaInvoiceItem.unit_price`（Line 37，所有行共用 USD 报价语义）
- 这套设计在业务中是**故意的一致选择**：订单行用 USD 报价、采购侧 RMB 转账各自处理

**结论**：
- ❌ 不新增 PI item 行级价格/货币列（破坏既有简洁设计）
- ❌ 不在 `ProductSearchItem` 返回 `price_rmb` / `currency`
- ✅ 仍要求 `unit_price`（USD 单价）作为订单行单价
- ✅ `PIInvoiceItemCreate` schema 仅需加 `customer_model` / `product_id`（本来 `product_id` 已声明，仅缺 customer_model）

**修复（最小改动）**：

1. **前端 payload**：
   ```ts
   items: [{
     product_id: form.product_id ?? null,         // P0-3 必填
     quantity: form.quantity,
     unit_price: form.unit_price,                  // USD 单价
     customer_code: form.customer_code,
     customer_model: form.customer_model || undefined,  // P0-4
     oe_number: form.oe_number || undefined,
     detail_desc: form.detail_desc || undefined,
   }],
   ```

2. **后端 schema 扩展**（`backend/schemas/pi.py:13`）：
   ```python
   class PIInvoiceItemCreate(BaseModel):
       product_id: Optional[int] = None
       quantity: float
       unit_price: float
       oe_number: Optional[str] = None
       customer_code: Optional[str] = None
       customer_model: Optional[str] = None     # ✅ 新增
       detail_desc: Optional[str] = None
       remark: Optional[str] = None
       # ❌ 不加 currency / price_usd / price_rmb
   ```

3. **create_pi 写入 `customer_model`**（`crud/pi.py:48-61`）：
   ```python
   db_item = PiProformaInvoiceItem(
       ...
       product_id=item.product_id,
       customer_model=item.customer_model,        # ✅ 写入
       # 不写 price_usd / price_rmb / currency（PI item 不保留这些）
       ...
   )
   ```

4. **§4.2.5 表单回填映射表（最终版）**：

| 表单字段 | 取值来源 | 备注 |
|---|---|---|
| `form.customer_code` | `item.customer_code \|\| item.product_code \|\| ''` | |
| `form.customer_model` | `item.customer_model \|\| ''` | |
| `form.oe_number` | `item.oes[0] \|\| ''` | OE 关联表首行（主 OE 优先） |
| `form.unit_price` | `item.price_usd ?? 0` | USD 单价（业务唯一币种） |
| `form.product_id` | `item.id` | **P0-3 必填** |
| `form.customer_id` | `item.customer_id` | |
| `form.detail_desc` | `item.detail_desc \|\| item.product_name \|\| ''` | |
| ~~`form.currency`~~ | ❌ 不存在 | 业务仅 USD，不需要前端字段 |

5. **onProductSelect 实现**：
   ```ts
   function onProductSelect(item: ProductSearchItem) {
     selectedProduct.value = item
     form.customer_id    = item.customer_id
     form.product_id     = item.id              // ✅ P0-3
     form.customer_code  = item.customer_code || item.product_code || ''
     form.customer_model = item.customer_model || ''
     form.oe_number      = item.oes[0] || ''
     form.unit_price     = item.price_usd ?? 0  // USD
     form.detail_desc    = item.detail_desc || item.product_name || ''
   }
   ```

6. **未来扩展**: 如果将来业务需要多币种，按以下步骤扩展（**不在本次实现范围**）：
   - alembic 迁移加 3 列到 `pi_proforma_invoice_item`：`currency` / `price_usd` / `price_rmb`
   - 更新 `PIInvoiceItemCreate` schema + `create_pi_invoice` CRUD
   - 在 `ProductSearchItem` 加 `currency` 字段
   - onProductSelect 用 `form.unit_price = item.currency === 'RMB' ? price_rmb * rate : price_usd` 决定

**回填校验**：如果 `form.customer_code` 为空，前端提示用户"该产品未设客户编号，请手动填写"，不阻断；保存时若 `customer_code` 为空 → 后端 Pydantic 不报错，但 PI item 行的 product_id 与 customer_code 至少要有一个（业务约定）。

### 4.3 ProductEditDialog 字段保存

**文件**: `frontend/src/components/order/ProductEditDialog.vue`
**位置**: L73-101 产品名称相关字段 + L102-111 OE 字段

#### 4.3.1 名称字段 — 无需修改

经核实：
- `useProductEdit.saveField` 已经把 4 个名称字段正确写入 `pi_proforma_invoice_item` 表（见 §1.4 表）。
- `ProductEditDialog.vue` L77/84 当前调用是 `saveField('detail_desc', ...)` / `saveField('detail_desc_en', ...)`，对应后端 PI item 表上的列，已经能正确保存。
- `useProductEdit.ts:30` 还有一层映射逻辑：`'detail_desc'` 显示为 `'product_name'`，`'detail_desc_en'` 显示为 `'product_name_en'`。这是 UI 层适配，保持不动。

**结论**: 前端无需修改 `saveField` 键名（修改会破坏现有保存链路）。

#### 4.3.2 OE 字段保存 — P1-4 接口决策

L102-111 的 `saveField('oe_number', form.oe_number)` 替换为：

```ts
async function saveOeField(value: string) {
  if (!productId.value) return
  const list = productSearchService.splitOeInput(value || '')
  await customerProductsApi.bulkSyncOes(productId.value, list)
  // 不再走通用 saveField（避免覆盖 PrdCustomerProduct.oe_number 旧字段）
}
```

**后端接口决策（P1-4 修复）**:

| 选项 | 优点 | 缺点 |
|---|---|---|
| A. 复用 `oes/batch`（追加语义）+ 前端先 GET 再 DELETE 多次 | 无新接口 | 4 步操作，部分失败易脏数据 |
| B. **新增 `oes/bulk-sync`**（POST，先删后增） | **单事务原子**，前端 1 个请求 | 新 handler |

**选 B**，handler 规格：

```
POST /api/customer-products/{product_id}/oes/bulk-sync
Content-Type: application/json

{
  "oes": ["601", "750", "AXMC"],        // 必填，可空数组（清空）
  "set_first_as_primary": true           // 可选，默认 true：列表首条做主 OE
}

→ 200 {
  "added": 3,
  "removed": 5,
  "total": 3,
  "primary_oe": "601"
}
```

**服务端规则**：

1. **事务**: 整个删除 + 插入用单个 SQLAlchemy session.begin() 包裹，任何异常整体回滚。
2. **去重**: 列表内 `set(oes)` 去空 + 去前后空格；DB 端利用 `UNIQUE(customer_product_id, oe_number)` 约束去重。
3. **主 OE 规则**:
   - `set_first_as_primary=true` 时：把列表首条设为 `is_primary=true`，其余为 `false`。
   - 列表为空时：清除所有现有 OE 的 `is_primary` 标记。
4. **删除行为**: 先按 `customer_product_id` DELETE 全部 `prd_customer_product_oe`，再 INSERT。
5. **不可变字段**: `customer_product_id`、`id`、`created_at` 不变。
6. **错误码**: 400（入参非数组）、404（产品不存在）、500（DB 异常，回滚）。
7. **审计日志**: 写入 `[product_search] bulk_sync product={id} added={n} removed={m}`，便于排查。

### 4.4 接入点

#### A. `NewOrderDialog.vue` L223-271
删除：radio group（searchMode）、autocomplete、select 三件套。
替换为：
```vue
<ProductSearchSelect
  v-model="selectedProduct"
  :customer-id="form.customer_id"
  placeholder="搜索 OE号 / 客户型号 / 产品名称"
  @select="onProductSelect"
/>
```
`onProductSelect(item)` 直接回填订单行，无需再走 `selectedProductIndex`。

#### B. `ProductManagement.vue` 顶部搜索框
替换内部搜索逻辑，复用同一组件，结果点击后跳转 `/products/{id}` 或打开 `ProductEditDialog`。

---

## 5. 数据契约（接口对齐）

### Request
```
GET /api/customer-products/search?keyword=750&limit=20&customer_id=1
```

### Response 200
```json
{
  "results": [
    {
      "id": 123,
      "customer_id": 1,
      "customer_name": "ACME Corp",
      "customer_model": "ACM-750",
      "product_name": "750 刹车片",
      "product_name_en": "Brake Pad 750",
      "product_short_name": "刹车片",
      "product_short_name_en": "BP750",
      "detail_desc": "适用 750 系列，前刹",
      "brand": "ACME",
      "customer_code": "A01S01240001",
      "product_code": "A01S01240001",
      "price_usd": 12.5,
      "image_url": "/static/uploads/123_main.jpg",
      "sub_images": ["/static/uploads/123_2.jpg"],
      "oes": ["601", "750", "AXMC"],
      "matched_in": ["oe", "product_name"],
      "match_score": 60.0
    }
  ],
  "total": 1
}
```

### 错误
- 400: `keyword` 为空或长度超限
- 500: DB 异常，body `{ detail: "search failed: ..." }`

---

## 6. 错误处理

| 层级 | 错误 | 处理 |
|------|------|------|
| 后端 | keyword 缺失 / 超长 | 422 由 FastAPI 自动返回 |
| 后端 | DB 异常 | 500 + 日志 `[product_search] {traceback}` |
| 前端 service | axios 4xx/5xx | 抛 `Error`，组件 catch 后显示 `<el-empty>` + 重试按钮 |
| 前端 service | **取消请求** | 用 **`axios.isCancel(error)`** 检测（P2-2 修正：`AbortController` 在 `axios` 体系下抛 `CanceledError`，不是 `AbortError`）。静默忽略，不提示，不写 ElMessage |
| 前端组件 | 防抖期间旧请求 | `controller.abort()` + 忽略 |
| 前端组件 | highlight 空 keyword | `splitForHighlight` 返回单段不命中，按原文本返回 |

---

## 7. 测试

### 7.1 后端 pytest（新增 `backend/tests/test_product_search.py`）
1. **精确 customer_model**: 插入 `customer_model="ABC-750"`，搜 `"ABC-750"` → score 100，matched_in 含 `customer_model`
2. **部分 customer_model**: 搜 `"ABC"` → score 80
3. **产品中文全称匹配**: 搜 `"刹车片"`，`product_name="750 刹车片"` → score 60，matched_in 含 `product_name`
4. **产品英文全称匹配**（PI item 路径）: 在 `pi_proforma_invoice_item` 表插入 `detail_desc_en="Brake Pad 750"`，关联到某 PrdCustomerProduct，搜 `"brake"` → 命中
5. **产品中文简称匹配**（PI item 路径）: 在 PI item 插入 `product_short_name="刹车片"`，搜 `"刹车"` → 命中
6. **产品英文简称匹配**（PI item 路径）: 在 PI item 插入 `product_short_name_en="BP750"`，搜 `"bp"` → 命中
7. **OE 子串匹配（单 token）**: 插入 `oes=["601","750","AXMC"]`，搜 `"750"` → score 50，matched_in 含 `oe`
8. **OE 多 token 拆分匹配**: 插入 `oes=["601","750","AXMC"]`，搜 `"601, 750 / AXMC"` → 必须返回该条
9. **OE 部分 token 命中**: 插入 `oes=["601","750","AXMC"]`，搜 `"ax"` → 命中（大小写不敏感子串）
10. **多匹配项排序**: 插入多条 candidate，断言按 score 降序
11. **customer_id 过滤（P0-1）**: 插入客户 A、B 各一条相同型号的产品，`customer_id=A` 搜索返回**只含 A 的那条**
12. **keyword 边界**: 空串 → 422；长度 101 → 422
13. **下单回填字段存在性**: response 至少含 `customer_code` / `price_usd` 字段（缺一即失败）；**不应**返回 `price_rmb` / `currency` 字段（P1-6 方案 1：业务仅支持 USD）
14. **OE 命中也返回名称字段（P1-5）**: 先在 PI item 写入产品 A 的 `product_short_name="刹车片"`，再在客户产品表把 customer_model 改为唯一值，搜索该 customer_model → 响应里 product_short_name 仍是 "刹车片"
15. **下单 product_id 写入**: 提交 PI 时 payload.items[0].product_id 不为 null，验证 `pi_proforma_invoice_item.product_id` 等于该值（P0-3）
16. **下单 customer_model 写入**: payload.items[0].customer_model 不为 null，验证 PI item.customer_model 一致（P0-4）
17. **仅 PI item detail_desc 命中（P0-6）**: `PrdCustomerProduct.product_name` 为 null，PI item.detail_desc="刹车片"，搜索 "刹车" → 命中，product_name 正确返回 "刹车片"
18. **仅 PI item customer_model 命中（P0-6）**: `PrdCustomerProduct.customer_model` 为 null，PI item.customer_model="ABC-750"，搜索 "ABC-750" → 命中，customer_model 正确返回
19. **已删除 PI item 不命中（P1-8）**: PI item 已软删除（`is_deleted=True`），搜索其 detail_desc → **不返回**
20. **已删除 PrdCustomerProduct 不返回（P0-8）**: `PrdCustomerProduct.deleted_at` 已设，客户型号为 "DELETED"，搜索 "DELETED" → **不返回**
21. **sub_images 解析**: PrdCustomerProduct.sub_images='["img2.jpg","img3.jpg"]'，搜索结果 item.sub_images 长度为 2；异常值 `"invalid json"` → 返回空数组，不抛错
22. **matched_in 映射正确（P0-6 / P0-7）**: PI item.detail_desc 命中，matched_in 含 "product_name"（而非原始键 "detail_desc"）；PI item.customer_model 命中，matched_in 含 "customer_model"

### 7.2 前端 vitest（新增 `frontend/src/api/__tests__/productSearch.test.ts`）
1. `splitForHighlight("刹车片 750", "750")` → `[{ text: "刹车片 ", hit: false }, { text: "750", hit: true }, ...]`，**不返回 HTML 字符串**
2. `splitForHighlight("a.b", ".")` → 不抛错，正则元字符正确转义
3. **XSS 防御**: `splitForHighlight("<script>alert(1)</script>", "alert")` 返回纯文本段，组件模板用 `{{ }}` 插值，**脚本不会执行**
4. `splitOeInput("601, 750 / AXMC;789")` → `["601","750","AXMC","789"]`
5. `splitOeInput("")` → `[]`
6. `splitOeInput(",,,")` → `[]`（全分隔符）

### 7.3 组件 vitest（`ProductSearchSelect.test.ts`）
1. 输入"750"，mock service 返回 1 条 → 下拉显示
2. 选中 → emit `update:modelValue` + `select`
3. 连续输入 3 次 → 实际调用 service 次数 ≤ 2（防抖）
4. 组件卸载 → 取消进行中请求

---

## 8. 迁移与回滚

- **OE 拆分迁移**: 现有 `PrdCustomerProductOE` 表已有数据，新 `bulk-sync` 接口仅替换该 customer_product_id 下的所有 OE，不动其他表。
- **新搜索接口可灰度**: 引入 `USE_PRODUCT_SEARCH` feature flag（前端常量）：
  - `true` → `<ProductSearchSelect>` 走 `/api/customer-products/search`
  - `false` → 保留 NewOrderDialog 现有的三件套 + `PRODUCT_CUSTOMER.search` 老 fallback（**老路径会 404**，仅作为界面层兼容，保留代码但不期望其工作；后续彻底删除）
  - 通过修改 `frontend/src/config/featureFlags.ts` 单文件切换
- **ProductSearchSelect 接入**: NewOrderDialog 旧 `searchProducts` 函数保留作为 fallback 注释，待新组件稳定后删除。
- **不回滚到不存在的旧接口**：经过核实，**没有**"/api/products/search 能完成多字段搜索"的旧实现可回滚（`backend/routers/product.py:25` 的 `/search` 是基于 `PrdProduct` 单表 ILIKE，**不包含 `customer_model` / PrdCustomerProductOE / 价格字段**）。回滚策略只通过 feature flag 切到旧三件套。

---

## 9. 待办 / 风险

| 风险 | 缓解 |
|------|------|
| `sub_images` 字段历史脏数据非 JSON | 解析失败回退 `[]`，加日志 |
| `customer_model` NULL 占比较多 | score 计算先判空再 ILIKE |
| 高亮 XSS（P1-3） | **`splitForHighlight` 不返回 HTML**；模板用 `<template v-for>` + `<em>` + `{{ }}` 插值；即使是 `<script>alert(1)</script>` 也会作为文本原样显示 |
| `customer_product_id` 旧列名 vs 新列名 | 以现有 ORM 关系为准，不改字段名 |
| LIMIT 200 排序不可靠（P1-1） | **不**在 SQL 截断，改为分字段独立查询 + 合并去重，最后按 score desc Python 截 limit |
| 名称字段数据来源（P1-2） | 不动 PrdCustomerProduct 表结构；跨表查询取最近一次 PI item 的 `detail_desc_en` / `product_short_name` / `product_short_name_en` |
| OE 全替换接口（P1-4） | 新增 `oes/bulk-sync`，单事务原子；前端 1 个请求；显式处理去重 + 主 OE |
| `customer_id` 过滤缺失（P0-3） | 4 组候选查询全部加 `if customer_id is not None` 过滤 PrdCustomerProduct.customer_id；PI name 过滤走 `PiProformaInvoice.customer_id`（JOIN 主表） |
| 下单 payload 缺 product_id / customer_model（P0-3） | 前端 `payload.items[0]` 必带 `product_id`；后端 `PIInvoiceItemCreate` schema 显式加 `customer_model` 字段（业务仅 USD，无需货币字段） |
| 通过 OE/型号命中时无名称字段展示（P1-5） | 候选集确定后再统一加载"全部候选产品最近一次 PI item"作为展示用，**覆盖**原始 `latest_name_map` |
| 价格币种混乱（P1-6） | 业务当前**仅支持 USD**：PI item 不保留 `price_usd`/`price_rmb`/`currency` 行级列；下单 `unit_price` 直接传 USD；未来扩展按 §4.2.5 第 6 步 |
| PI item detail_desc/customer_model 未加入候选（P0-6） | `pi_name_match_q` 的 OR 条件必须含 `PiProformaInvoiceItem.detail_desc` 和 `.customer_model`；精排时 `_get_name_fields()` 已实现 PI item 优先 fallback |
| 返回值 Schema 不符（P0-7） | 必须通过 `build_search_item()` 返回完整 `ProductSearchItem` 对象；`matched_in` 做键映射转换；`sub_images` 真实解析 JSON |
| PrdCustomerProduct.deleted_at 未过滤（P0-8） | 最终产品加载 `.filter(PrdCustomerProduct.deleted_at.is_(None))`；避免已删除产品从 PI item 重新出现 |
| 已删除 PI item 名称参与搜索（P1-8） | 两处 latest PI 子查询均加 `is_deleted == False`；JOIN 后额外兜底 `filter` |
| customer_name 类型不一致（P2） | `ProductSearchItem.customer_name` 声明为 `str | None`；serializer 返回 `p.customer.name if p.customer else ""`，两者一致 |
| N+1 查询风险（P2-3） | 最终产品加载时用 `joinedload`/`selectinload` 预加载 `customer`/`codes`/`oes`；不加则 20 条结果产生 60+ 条 SQL |
| 回滚策略指向不存在接口（P2-1） | 引入 `USE_PRODUCT_SEARCH` feature flag，回滚到旧三件套，**不回滚**到旧 `/api/products/search`（功能不完整） |
| AbortError/CanceledError（P2-2） | 用 `axios.isCancel(error)` 判定；客户端 `AbortController` 实际抛 `CanceledError` |
| 大数据量下 ILIKE 慢 | 全表 ILIKE 6 次 + Python score 在 < 5k 行客户产品时 < 200ms；如未来超 10k 行再评估 pg_trgm |
| 路由顺序错配（P0-1 路由顺序） | 新增 `/search` handler 必须放在 `@router.get("/{product_id}")` 之前，FastAPI 按声明顺序匹配 |

---

## 10. 文件清单

### 新建
- `backend/crud/product_search.py`
- `backend/schemas/product_search.py`
- `backend/tests/test_product_search.py`
- `backend/routers/customer_product.py`（**替换**现有 `/search` handler 为增强版）
- `frontend/src/api/productSearch.ts`
- `frontend/src/api/__tests__/productSearch.test.ts`
- `frontend/src/components/common/ProductSearchSelect.vue`
- `frontend/src/components/common/__tests__/ProductSearchSelect.test.ts`
- `frontend/src/config/featureFlags.ts`（`USE_PRODUCT_SEARCH: true`，回滚开关）

> ⚠️ **不**做 alembic 迁移：`prd_customer_product` 表结构已满足需求，名称字段实际存在 `pi_proforma_invoice_item` 表（无需迁移）。

### 修改
- ~~`backend/models/customer_product.py`（加 3 列）~~ **不需要**
- ~~`backend/schemas/customer_product.py`（加 3 字段）~~ **不需要**
- `backend/crud/product_search.py`（新建：`split_oe_tokens` + 分字段候选查询 + Python score 精排）
- `backend/schemas/product_search.py`（新建：`ProductSearchItem` + `ProductSearchResponse`）
- `backend/routers/customer_product.py`（**新增** `/search` handler + **新增** `/{product_id}/oes/bulk-sync` handler；引用 `PiProformaInvoiceItem` 做跨表查询）
- `backend/schemas/pi.py`（`PIInvoiceItemCreate` 加 `customer_model` 字段；**不加** currency/price_usd/price_rmb 行级字段）
- `backend/crud/pi.py`（`create_pi_invoice` 写入 `customer_model`；**不写** PI item 行级货币/价格列）
- `backend/tests/test_product_search.py`（pytest 覆盖 P0-1 / P0-3 / P0-4 / P1-1 / P1-2 / P1-3 / P1-4 / P1-5）
- `frontend/src/api/endpoints.ts`（新增 `PRODUCT_SEARCH.recommend = '/api/customer-products/search'`，`PRODUCT_CUSTOMER.search` 改为转发到该地址并标记 `@deprecated`）
- `frontend/src/components/order/NewOrderDialog.vue`：
  - L223-271 替换为 `<ProductSearchSelect>`；`onProductSelect` 按 §4.2.5 映射回填（**不涉及 currency**，业务仅 USD）
  - 下单 `payload.items[0]` 必须含 `product_id` / `customer_model`（P0-3 / P0-4）
- `frontend/src/components/order/SupplementDialog.vue`（L252 同样替换为 `<ProductSearchSelect>`，复用同一 service + 组件）
- `frontend/src/views/product/ProductManagement.vue`（顶部搜索接入）
- `frontend/src/components/order/ProductEditDialog.vue`
  - **不动** L77 / L84 saveField 键（已正确写入 PI item 表，见 §1.4）
  - L109 OE 字段保存改为 `saveOeField` → 调 `bulkSyncOes`（参考 §4.3.2）
- `docs/spec.md`（在常用接口约定章节补充 `/api/customer-products/search`；移除 `/api/product-customer/search` 条目）

### 删除
- `backend/routers/product_customer.py`（**已删除**，前端零引用；底层 `PrdProductCustomer` 模型仍由其他模块间接使用，**不删除 model/crud/schema**，避免破坏面扩大）

---

## 11. 验收标准

### P0 修复（P0-1 / P0-2 / P0-3 / P0-4 / P0-6 / P0-7 / P0-8 必须全部通过）
- **P0-1 接口路径**: 前端调用 `GET /api/customer-products/search`，后端 200；旧路径 `/api/product-customer/search` 不再被前端引用。
- **P0-2 下单回填字段**: 选择搜索结果后，`form.customer_code` / `form.customer_model` / `form.oe_number` / `form.unit_price` / `form.product_id` / `form.customer_id` 全部正确回填（即使响应里某些字段为 null 也不报错，UI 给出友好提示）。
- **P0-3 customer_id 过滤 + product_id 入 payload**:
  - **customer_id 过滤**: 搜索时传 `customer_id` 参数，4 类候选都被过滤。验证：插入客户 A、B 各一条相同型号的产品，`customer_id=A` 搜索返回只含 A 的那条。
  - **OE 多 token 拆分**: 录入 `601,750,AXMC` 保存后，搜索 `601, 750 / AXMC`（带分隔符的整串）必须返回该条；搜索 `750` 也命中；搜索 `ax`（小写片段）也命中。
  - **product_id 入 payload**: 下单提交 `payload.items[0]` 必须含 `product_id`，后端 `crud.pi.create_pi_invoice` 必须写入 `pi_proforma_invoice_item.product_id`。
- **P0-4 customer_model 入 payload**: `PIInvoiceItemCreate` schema 必须显式声明 `customer_model` 字段；下单后 PI item 的 `customer_model` 与表单一致。

### P1 修复（P1-1 / P1-2 / P1-3 / P1-4 / P1-5 / P1-6 必须全部通过）
- **P1-1 排序可靠性**: 数据库中存在大量客户产品时，精确匹配 `customer_model == kw` 的条目**必须出现在结果前列**，不能因为 LIMIT 截断而消失。验证：插入 500 条随机产品 + 1 条精确匹配，搜索该精确型号应返回首条。
- **P1-2 名称字段闭环**: 名称字段的**唯一数据源**是 `pi_proforma_invoice_item` 表（`detail_desc_en` / `product_short_name` / `product_short_name_en`）。搜索响应里这 3 个字段来自最近一次 PI item。前端 `saveField` 无需修改键名。验证：在 PI item 里设 `product_short_name = "刹车片"`，搜索 "刹车" 应命中。
- **P1-3 XSS 防御**: 组件不应使用 `v-html`；含恶意 HTML 的产品名应作为文本原样展示，不执行。验证：在 `PrdCustomerProduct.product_name` 写入 `<script>alert(1)</script>`，搜索 → 页面不应弹窗。
- **P1-4 OE 批量同步**: `POST /api/customer-products/{id}/oes/bulk-sync` 单事务原子，去重，主 OE = 首条，清空时主 OE 也清除。
- **P1-5 非名称命中也返回名称字段**: 通过 OE / 客户型号 命中的产品，响应 `product_name_en` / `product_short_name*` **必须有值**（来自该产品最近一次 PI item）。验证：先在 PI item 里写入产品 A 的 `product_short_name = "刹车片"`，再在客户产品表把 customer_model 改为唯一值，搜索该 customer_model → 响应里 product_short_name 仍是 "刹车片"。
- **P1-6 货币字段（方案 1：仅 USD）**: 响应**不返回** `currency` / `price_rmb`；搜索结果显示的"价格货币"由 PI 主表 `currency` 决定（默认 USD）；下单单 `unit_price` 按 USD 处理。**未来多币种扩展路径见 §4.2.5 第 6 步。**
- **P1-7 detail_desc 精排**: `PrdCustomerProduct.detail_desc` 独立参与精排（score=30），避免仅命中详细描述的商品 score 为 0、matched_in 缺失。
- **P1-8 已删除 PI item 过滤**: 两处 latest PI 子查询（`latest_pi_item_sq` + `latest_pi_all_sq`）均加 `is_deleted == False`；子查询 JOIN 后额外加兜底 `filter`；避免已软删除 PI 的名称参与搜索。
- **P2-3 N+1 防护**: 最终加载 `PrdCustomerProduct` 时用 `joinedload(customer)` / `selectinload(codes)` / `selectinload(oes)` 预加载关联，20 条结果总共 4 条 SQL，而非 60+ 条。

### 业务验收
1. ProductEditDialog 中英文全称 + 简称 blur 后重新打开仍能看到值（写入 PI item 表）。
2. NewOrderDialog 录入"601,750,AXMC"保存后，搜索"750"返回该条，搜索"601"也返回。
3. 录入产品简称"刹车片"，搜索"刹车"命中，搜索"片"也命中。
4. 录入产品英文名"Brake Pad 750"，搜索"brake"命中（不区分大小写）。
5. 搜索"无此编号"返回 0 条 + `<el-empty>` 占位。
6. 搜索结果命中字段高亮（红字），hover 副图缩略图可预览大图。
7. 客户型号精确匹配排第一（score 100），OE 子串匹配排在其后（score 50）。
8. `match_score` 在前端不展示（仅用于排序）。
9. 后端 pytest 通过（覆盖 4 个名称字段 + 客户型号 + OE + 描述 + 下单回填字段 + XSS 输入 + customer_id 过滤 + product_id 写入），前端 vitest 通过。
10. `endpoints.ts` 是单一来源，切换搜索接口仅改一处常量。
11. NewOrderDialog 下单流程：选完产品 → 创建订单 → 后端 PI item 写入 `customer_code` / `customer_model` / `unit_price` / `oe_number` / **`product_id`** 与表单一致。
12. `USE_PRODUCT_SEARCH` feature flag 切到 false 后，搜索降级到旧三件套（不期望工作，但页面不崩）。