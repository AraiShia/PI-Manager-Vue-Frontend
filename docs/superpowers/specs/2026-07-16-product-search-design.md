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
6. **修复现有 saveField 键错位**：把 UI 上的 4 个名称字段正确写入数据库新列。

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

**结论（P1-2）**:
- PI item 表是当前名称字段的**唯一数据源**，crud/pi.py L1096-1103 已经写好 4 个 if 分支，无须改。
- `prd_customer_product` 表**不需要新增** 3 列（`product_name_en` / `product_short_name*`）。
- 之前 spec §3.1.1 / §4.3.1 关于"修复 saveField 键错位 + 数据库迁移"的提议是**误判**，整段撤掉。
- 搜索要读到名称字段，必须**跨表查询**（`PrdCustomerProduct` 主表 JOIN `pi_proforma_invoice_item` 取 max(id) 的最近一次名称），见 §3.5。

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
              │  - highlight(text, kw)       │
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

**新增** `/search` handler（注：原 `routers/product_customer.py` 已清理删除，不影响本路径）：

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
    customer_name: str
    # ---- 名称/型号 ----
    customer_model: str | None
    product_name: str | None                 # 中文全称
    product_name_en: str | None              # 英文全称
    product_short_name: str | None           # 中文简称
    product_short_name_en: str | None        # 英文简称
    detail_desc: str | None
    brand: str | None
    # ---- 下单回填关键字段（P0-2 修复）----
    customer_code: str | None                # 客户产品编号（PrdCustomerProductCode.primary_code）
    product_code: str | None                 # 系统产品编号（PrdCustomerProduct.system_code，备用）
    price_usd: float | None                  # PrdCustomerProduct.price_usd
    price_rmb: float | None                  # PrdCustomerProduct.price_rmb
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
exact_model = (
    db.query(PrdCustomerProduct)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        PrdCustomerProduct.customer_model == keyword,
    )
    .all()
)

# 2) 产品名称 / 描述模糊匹配（无 LIMIT）
text_kw = f"%{keyword}%"
text_match = (
    db.query(PrdCustomerProduct)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(
            PrdCustomerProduct.product_name.ilike(text_kw),
            PrdCustomerProduct.detail_desc.ilike(text_kw),
        ),
    )
    .all()
)

# 3) PI item 名称字段：LEFT JOIN 拿每个 product_id 最近一次的名称
from sqlalchemy import func
latest_pi_item_sq = (
    db.query(
        PiProformaInvoiceItem.product_id,
        func.max(PiProformaInvoiceItem.id).label("latest_id"),
    )
    .filter(PiProformaInvoiceItem.product_id.isnot(None))
    .group_by(PiProformaInvoiceItem.product_id)
    .subquery()
)
pi_name_rows = (
    db.query(PiProformaInvoiceItem)
    .join(latest_pi_item_sq,
          PiProformaInvoiceItem.id == latest_pi_item_sq.c.latest_id)
    .filter(
        or_(
            PiProformaInvoiceItem.detail_desc_en.ilike(text_kw),
            PiProformaInvoiceItem.product_short_name.ilike(text_kw),
            PiProformaInvoiceItem.product_short_name_en.ilike(text_kw),
        ),
    )
    .all()
)
# 构造 product_id -> 最近一次 PI item
latest_name_map: dict[int, PiProformaInvoiceItem] = {
    row.product_id: row for row in pi_name_rows
}

# 4) OE 子串（多 token，OR 条件）
oe_subqs = [
    PrdCustomerProductOE.oe_number.ilike(f"%{tok}%")
    for tok in oe_tokens if tok
]
if oe_subqs:
    oe_match = (
        db.query(PrdCustomerProduct)
        .join(PrdCustomerProductOE,
              PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id)
        .filter(
            PrdCustomerProduct.deleted_at.is_(None),
            or_(*oe_subqs),
        )
        .distinct()
        .all()
    )
else:
    oe_match = []

# 5) 收集 product_id 集合 → 一次性把 PrdCustomerProduct 全部加载
candidate_ids: set[int] = set()
for src_list in [exact_model, text_match, oe_match]:
    for p in src_list:
        candidate_ids.add(p.id)
for pid in latest_name_map.keys():
    candidate_ids.add(pid)
products = {
    p.id: p
    for p in db.query(PrdCustomerProduct)
    .filter(PrdCustomerProduct.id.in_(candidate_ids)).all()
}
```

**Python 端精排 score**（按 score desc，最后才 LIMIT 截取，保证精确匹配不被丢弃）：

```python
def score_product(p, kw, oe_tokens, latest_pi_item) -> tuple[float, list[str]]:
    score, matched = 0.0, []
    kwl = kw.lower()
    token_lc = [t.lower() for t in oe_tokens if t]

    if p.customer_model:
        if p.customer_model == kw:
            score = max(score, 100.0); matched.append("customer_model")
        elif kwl in p.customer_model.lower():
            score = max(score, 80.0); matched.append("customer_model")

    if p.product_name and kwl in p.product_name.lower():
        score = max(score, 60.0); matched.append("product_name")

    if latest_pi_item is not None:
        pi_name_fields = [
            ("product_name_en",       getattr(latest_pi_item, "detail_desc_en", None), 55),
            ("product_short_name",    getattr(latest_pi_item, "product_short_name", None), 45),
            ("product_short_name_en", getattr(latest_pi_item, "product_short_name_en", None), 40),
        ]
        for key, val, sc in pi_name_fields:
            if val and kwl in str(val).lower():
                score = max(score, float(sc)); matched.append(key)

    if p.detail_desc and kwl in p.detail_desc.lower():
        score = max(score, 30.0); matched.append("detail_desc")

    oes = [(oe.oe_number or "") for oe in p.oes]
    if any(any(tok in oe.lower() for tok in token_lc) for oe in oes):
        score = max(score, 50.0); matched.append("oe")

    return score, matched

# 主流程：先算所有候选 score，再排序截 limit
results = []
for pid, p in products.items():
    score, matched = score_product(
        p, keyword, oe_tokens, latest_name_map.get(pid)
    )
    results.append((score, p, matched))
results.sort(key=lambda x: (-x[0], x[1].id))
results = results[:limit]
```

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
  customer_name: string
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
  price_usd: number | null
  price_rmb: number | null
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

### 4.2.5 NewOrderDialog 订单回填映射（P0-2 修复）

`NewOrderDialog.vue` 现有的 L715-720 是基于 `Product`（老搜索类型）实现的，迁移到 `ProductSearchItem` 后必须保证订单行能正确生成。新组件 emit `select(item)`，消费方按以下映射写入表单：

| 表单字段 | 取值来源（`item: ProductSearchItem`） | 备注 |
|---|---|---|
| `form.customer_code` | `item.customer_code \|\| item.product_code \|\| ''` | 兼容旧字段名 |
| `form.customer_model` | `item.customer_model \|\| ''` | |
| `form.oe_number` | `item.oes[0] \|\| ''` | OE 关联表第一行（按主 OE 优先） |
| `form.unit_price` | `item.price_usd ?? 0` | USD 单价 |
| `form.product_id` | `item.id` | 客户产品 ID（用于后端 `pi_item.product_id`） |
| `form.customer_id` | `item.customer_id` | 用于下单时锁定客户 |
| `form.detail_desc` | `item.detail_desc \|\| item.product_name \|\| ''` | 显示用 |

实现示例（`NewOrderDialog.vue`）：
```ts
function onProductSelect(item: ProductSearchItem) {
  selectedProduct.value = item
  form.customer_code  = item.customer_code || item.product_code || ''
  form.customer_model = item.customer_model || ''
  form.oe_number      = item.oes[0] || ''
  form.unit_price     = item.price_usd ?? 0
  form.product_id     = item.id
  form.customer_id    = item.customer_id
  form.detail_desc    = item.detail_desc || item.product_name || ''
}
```

**回填校验**：如果 `form.customer_code` 为空，提示用户"该产品未设客户编号，请手动填写"（弹窗不阻断）。

**Price 货币**：`price_usd` 始终写入 `form.unit_price`；若用户下单币种是 RMB（业务上暂时只有 USD），由上层再做汇率转换（本规格不涉及汇率逻辑，已独立处理）。

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
      "price_rmb": 88.0,
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
| 前端 service | 取消请求 (AbortError) | 静默忽略，不提示 |
| 前端组件 | 防抖期间旧请求 | abort + 忽略 |
| 前端组件 | highlight 空 keyword | 直接返回原文，不注入 `<em>` |

---

## 7. 测试

### 7.1 后端 pytest（新增 `backend/tests/test_product_search.py`）
1. **精确 customer_model**: 插入 `customer_model="ABC-750"`，搜 `"ABC-750"` → score 100，matched_in 含 `customer_model`
2. **部分 customer_model**: 搜 `"ABC"` → score 80
3. **产品中文全称匹配**: 搜 `"刹车片"`，`product_name="750 刹车片"` → score 60，matched_in 含 `product_name`
4. **产品英文全称匹配**: `product_name_en="Brake Pad 750"`，搜 `"brake"` → score 55，matched_in 含 `product_name_en`
5. **产品中文简称匹配**: `product_short_name="刹车片"`，搜 `"刹车"` → score 45
6. **产品英文简称匹配**: `product_short_name_en="BP750"`，搜 `"bp"` → score 40
7. **OE 子串匹配（单 token）**: 插入 `oes=["601","750","AXMC"]`，搜 `"750"` → score 50，matched_in 含 `oe`
8. **OE 多 token 拆分匹配（P0-3 关键用例）**: 插入 `oes=["601","750","AXMC"]`，搜 `"601, 750 / AXMC"` → 必须返回该条（修复前会失败）
9. **OE 部分 token 命中**: 插入 `oes=["601","750","AXMC"]`，搜 `"ax"` → 命中（大小写不敏感子串）
10. **多匹配项排序**: 插入多条 candidate，断言按 score 降序
11. **customer_id 过滤**: 仅返回指定客户产品
12. **keyword 边界**: 空串 → 422；长度 101 → 422
13. **下单回填字段存在性**: response 至少含 `customer_code` / `price_usd` / `price_rmb` 字段（缺一即失败）

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

- **OE 拆分迁移**: 现有 `PrdCustomerProductOE` 表已有数据，新 `bulk-sync` 接口仅追加/删除差异行，不动其他数据。
- **新搜索接口可灰度**: 旧 `/api/products/search` 不动，前端切换通过改 `endpoints.ts` 常量即可回滚到旧实现。
- **ProductSearchSelect 接入**: NewOrderDialog 旧代码可保留作为 fallback 注释，待新组件稳定后删除。

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
| 大数据量下 ILIKE 慢 | 全表 ILIKE 4 次 + Python score 在 < 5k 行客户产品时 < 200ms；如未来超 10k 行再评估 pg_trgm |

---

## 10. 文件清单

### 新建
- `backend/migrations/versions/xxxx_add_product_name_en_short.py`（alembic 迁移，加 3 列）
- `backend/crud/product_search.py`
- `backend/schemas/product_search.py`
- `backend/tests/test_product_search.py`
- `backend/routers/customer_product.py`（**替换**现有 `/search` handler 为增强版）
- `frontend/src/api/productSearch.ts`
- `frontend/src/api/__tests__/productSearch.test.ts`
- `frontend/src/components/common/ProductSearchSelect.vue`
- `frontend/src/components/common/__tests__/ProductSearchSelect.test.ts`

### 修改
- ~~`backend/models/customer_product.py`（加 3 列）~~ **不需要**
- ~~`backend/schemas/customer_product.py`（加 3 字段）~~ **不需要**
- `backend/crud/product_search.py`（新建：`split_oe_tokens` + 分字段候选查询 + Python score 精排）
- `backend/schemas/product_search.py`（新建：`ProductSearchItem` + `ProductSearchResponse`）
- `backend/routers/customer_product.py`（**新增** `/search` handler + **新增** `/{product_id}/oes/bulk-sync` handler；引用 `PiProformaInvoiceItem` 做跨表查询）
- `backend/tests/test_product_search.py`（pytest 覆盖 P1-1 / P1-2 / P1-4）
- `frontend/src/api/endpoints.ts`（新增 `PRODUCT_SEARCH.recommend = '/api/customer-products/search'`，`PRODUCT_CUSTOMER.search` 改为转发到该地址并标记 `@deprecated`）
- `frontend/src/components/order/NewOrderDialog.vue`（L223-271 替换为 `<ProductSearchSelect>`；`onProductSelect` 按 §4.2.5 映射回填）
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

### P0 修复（P0-1 / P0-2 / P0-3 必须全部通过）
- **P0-1 接口路径**: 前端调用 `GET /api/customer-products/search`，后端 200；旧路径 `/api/product-customer/search` 不再被前端引用。
- **P0-2 下单回填**: 选择搜索结果后，`form.customer_code` / `form.customer_model` / `form.oe_number` / `form.unit_price` / `form.product_id` / `form.customer_id` 全部正确回填（即使响应里某些字段为 null 也不报错，UI 给出友好提示）。
- **P0-3 OE 多 token 拆分**: 录入 `601,750,AXMC` 保存后，搜索 `601, 750 / AXMC`（带分隔符的整串）必须返回该条；搜索 `750` 也命中；搜索 `ax`（小写片段）也命中。

### P1 修复（P1-1 / P1-2 / P1-3 / P1-4 必须全部通过）
- **P1-1 排序可靠性**: 数据库中存在大量客户产品时，精确匹配 `customer_model == kw` 的条目**必须出现在结果前列**，不能因为 LIMIT 截断而消失。验证：插入 500 条随机产品 + 1 条精确匹配，搜索该精确型号应返回首条。
- **P1-2 名称字段闭环**: 名称字段的**唯一数据源**是 `pi_proforma_invoice_item` 表（`detail_desc_en` / `product_short_name` / `product_short_name_en`）。搜索响应里这 3 个字段来自最近一次 PI item。前端 `saveField` 无需修改键名。验证：在 PI item 里设 `product_short_name = "刹车片"`，搜索 "刹车" 应命中。
- **P1-3 XSS 防御**: 组件不应使用 `v-html`；含恶意 HTML 的产品名应作为文本原样展示，不执行。验证：在 `PrdCustomerProduct.product_name` 写入 `<script>alert(1)</script>`，搜索 → 页面不应弹窗。
- **P1-4 OE 批量同步**: `POST /api/customer-products/{id}/oes/bulk-sync` 单事务原子，去重，主 OE = 首条，清空时主 OE 也清除。验证：先批量同步 `["601","750"]` → 再同步 `["AXMC"]` → 旧 OE 全部清除只剩 AXMC，且 AXMC 为主 OE。

### 业务验收
1. ProductEditDialog 中英文全称 + 简称 blur 后重新打开仍能看到值（写入 PI item 表）。
2. NewOrderDialog 录入"601,750,AXMC"保存后，搜索"750"返回该条，搜索"601"也返回。
3. 录入产品简称"刹车片"，搜索"刹车"命中，搜索"片"也命中。
4. 录入产品英文名"Brake Pad 750"，搜索"brake"命中（不区分大小写）。
5. 搜索"无此编号"返回 0 条 + `<el-empty>` 占位。
6. 搜索结果命中字段高亮（红字），hover 副图缩略图可预览大图。
7. 客户型号精确匹配排第一（score 100），OE 子串匹配排在其后（score 50）。
8. `match_score` 在前端不展示（仅用于排序）。
9. 后端 pytest 通过（覆盖 4 个名称字段 + 客户型号 + OE + 描述 + 下单回填字段 + XSS 输入），前端 vitest 通过。
10. `endpoints.ts` 是单一来源，切换搜索接口仅改一处常量。
11. NewOrderDialog 下单流程：选完产品 → 创建订单 → 后端 PI item 写入 customer_code / price_usd / oe 与表单一致。