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

### 1.4 现有中英文产品全称/简称字段的现状

`frontend/src/components/order/ProductEditDialog.vue` L73-101 已引入 4 个产品名称相关字段：

| UI 字段 | `form.*` | `saveField` 写入键 | 后端 `PrdCustomerProduct` 列 |
|---|---|---|---|
| 产品名称（中） | `form.product_name` | `detail_desc` | ✅ 有 `detail_desc` |
| 产品名称（英） | `form.product_name_en` | `detail_desc_en` | ❌ 无 |
| 简称（中） | `form.product_short_name` | `product_short_name` | ❌ 无 |
| 简称（英） | `form.product_short_name_en` | `product_short_name_en` | ❌ 无 |

意味着当前英文全称/中文简称/英文简称 blur 保存时**写到了不存在的列**，会丢数据。

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

### 3.1.1 数据库迁移（前置）

需先在 `prd_customer_product` 表补齐三列：

```python
# alembic revision
op.add_column("prd_customer_product",
    sa.Column("product_name_en", sa.String(200), nullable=True))
op.add_column("prd_customer_product",
    sa.Column("product_short_name", sa.String(100), nullable=True))
op.add_column("prd_customer_product",
    sa.Column("product_short_name_en", sa.String(100), nullable=True))
```

模型同步：
```python
# backend/models/customer_product.py
product_name_en = Column(String(200), comment="产品名称（英文）")
product_short_name = Column(String(100), comment="产品简称（中文）")
product_short_name_en = Column(String(100), comment="产品简称（英文）")
```

Schema 同步（`schemas/customer_product.py` 的 `CustomerProductUpdate` / `CustomerProductCreate` / `CustomerProductResponse` 各加 3 个 Optional 字段）。

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

#### 候选集（粗筛，LIMIT 200）

⚠️ **关键修复**: OE 字段必须按拆分后的 token 构造 `or_` 条件，否则单条 `ilike("%601,750,AXMC%")` 永远不命中单独存储的 "601"。

```python
# 文本字段（按整串 ILIKE；原始 keyword 本身就是用户搜索意图）
text_kw = f"%{keyword}%"
text_clauses = [
    PrdCustomerProduct.customer_model.ilike(text_kw),
    PrdCustomerProduct.product_name.ilike(text_kw),
    PrdCustomerProduct.product_name_en.ilike(text_kw),
    PrdCustomerProduct.product_short_name.ilike(text_kw),
    PrdCustomerProduct.product_short_name_en.ilike(text_kw),
    PrdCustomerProduct.detail_desc.ilike(text_kw),
]

# OE 字段：每个 token 单独 ILIKE，OR 连接
oe_clauses = [
    PrdCustomerProductOE.oe_number.ilike(f"%{tok}%")
    for tok in oe_tokens
]
# 防御：万一拆出来是空列表（keyword 全是分隔符），退化到整串匹配
if not oe_clauses:
    oe_clauses = [PrdCustomerProductOE.oe_number.ilike(text_kw)]

candidate_query = (
    db.query(PrdCustomerProduct)
    .outerjoin(PrdCustomerProductOE,
               PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(*text_clauses, *oe_clauses),
    )
    .distinct()
    .limit(200)
)
if customer_id is not None:
    candidate_query = candidate_query.filter(
        PrdCustomerProduct.customer_id == customer_id
    )
candidates = candidate_query.all()
```

#### 精排（Python 计算 match_score）
```python
def score_product(p: PrdCustomerProduct, kw: str, oe_tokens: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    matched: list[str] = []
    kwl = kw.lower()
    token_lc = [t.lower() for t in oe_tokens if t]

    # 客户型号精确 > 模糊（最高优先级，按整串匹配）
    if p.customer_model:
        if p.customer_model == kw:
            score = max(score, 100.0); matched.append("customer_model")
        elif kwl in p.customer_model.lower():
            score = max(score, 80.0); matched.append("customer_model")

    # 产品全称 / 简称（中文/英文，整串匹配）
    name_fields = [
        ("product_name",          p.product_name,          60),
        ("product_name_en",       p.product_name_en,       55),
        ("product_short_name",    p.product_short_name,    45),
        ("product_short_name_en", p.product_short_name_en, 40),
    ]
    for key, val, sc in name_fields:
        if val and kwl in val.lower():
            score = max(score, float(sc)); matched.append(key)

    # 详细描述
    if p.detail_desc and kwl in p.detail_desc.lower():
        score = max(score, 30.0); matched.append("detail_desc")

    # OE 号子串（按拆分后 token 命中）
    oes = [(oe.oe_number or "") for oe in p.oes]
    hit_oe = any(
        any(tok in oe.lower() for tok in token_lc)
        for oe in oes
    )
    if hit_oe:
        score = max(score, 50.0); matched.append("oe")

    return score, matched
```

#### OE 子串拆分
将 `keyword` 按 `[,\s/、;]+` 拆分，得到 `oe_substrings: set[str]`。
任一 `PrdCustomerProductOE.oe_number` 包含任一子串即视为 OE 命中。

#### 副图解析
`sub_images` 字段为 TEXT 存 JSON 数组字符串，Python 端 `json.loads` 失败时回退 `[]`。
异常一律 `except json.JSONDecodeError: return []`。

### 3.4 端点常量更新
**文件**: `frontend/src/api/endpoints.ts`
```ts
export const PRODUCT_SEARCH = {
  recommend: '/api/customer-products/search',  // P0-1 修复：与后端 router 前缀对齐
} as const
```
并删除（已不再使用）/ 留作占位的 `PRODUCT_CUSTOMER.search`（迁移 NewOrderDialog 至 `PRODUCT_SEARCH.recommend`）。

---

## 4. 前端设计

### 4.1 productSearchService

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

  /** 转义正则元字符 + 高亮 + 反注入 */
  highlight(text: string | null | undefined, keyword: string): string {
    if (!text) return ''
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return text.replace(
      new RegExp(`(${escaped})`, 'gi'),
      '<em class="search-hl">$1</em>'
    )
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
    <div class="ps-line ps-name" v-html="highlight(item.product_name, kw)"/>
    <div class="ps-line ps-name-en" v-html="highlight(item.product_name_en, kw)"/>
    <div class="ps-line ps-short">
      <span v-if="item.product_short_name"
            v-html="highlight(item.product_short_name, kw)"/>
      <span v-if="item.product_short_name_en" class="ps-short-en"
            v-html="highlight(item.product_short_name_en, kw)"/>
    </div>
    <div class="ps-line ps-model">
      <span class="ps-label">客户型号:</span>
      <span v-html="highlight(item.customer_model, kw)"/>
    </div>
    <div class="ps-line ps-oe">
      <span class="ps-label">OE:</span>
      <span v-for="(oe, i) in item.oes" :key="i" class="ps-oe-chip"
            v-html="highlight(oe, kw)"/>
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

### 4.3 ProductEditDialog 字段保存修正

**文件**: `frontend/src/components/order/ProductEditDialog.vue`
**位置**: L73-101 产品名称相关字段 + L102-111 OE 字段

#### 4.3.1 名称字段 saveField 修正

当前实现把 4 个字段保存到不存在的列（详见 §1.4），需要把 `saveField` 的入参改为正确键：

| UI | 改为 |
|---|---|
| `saveField('detail_desc', form.product_name)` | `saveField('product_name', form.product_name)` |
| `saveField('detail_desc_en', form.product_name_en)` | `saveField('product_name_en', form.product_name_en)` |
| `saveField('product_short_name', form.product_short_name)` | ✅（待模型加列） |
| `saveField('product_short_name_en', form.product_short_name_en)` | ✅（待模型加列） |

实现优先级：先迁移数据库 + Schema（§3.1.1），再改前端 saveField 键。

#### 4.3.2 OE 字段保存

L102-111 的 `saveField('oe_number', form.oe_number)` 替换为：

```ts
async function saveOeField(value: string) {
  const list = productSearchService.splitOeInput(value || '')
  await customerProductsApi.bulkSyncOes(productId.value, list)
  // 不再走通用 saveField（避免覆盖 PrdCustomerProduct.oe_number 旧字段）
}
```

**后端依赖**: OE 同步需要"全替换"语义，但现有 `POST /api/customer-products/{id}/oes/batch`（`customer_product.py:385-396`）只是**追加**，不删旧。

采用方案 A：**新增** `POST /api/customer-products/{id}/oes/bulk-sync`
- 接受 `{ oes: ["601", "750", "AXMC"] }`
- 内部按 `customer_product_id` 先 DELETE 全部 `PrdCustomerProductOE`，再 BATCH INSERT 新列表
- 返回 `{ added: number, removed: number, total: number }`

采用方案 B（保守）：复用现有 `oes/batch`，前端保存时先 `GET /oes` 拿到全部 id，再逐个 `DELETE`，最后 `POST /oes/batch`。**不推荐**：多步操作易出现部分失败导致数据不一致。

**本规格选方案 A**：在 `customer_product.py` 同文件内追加 `bulk_sync_oes` handler，路径 `/api/customer-products/{id}/oes/bulk-sync`。

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
1. `highlight("刹车片 750", "750")` → 含 `<em class="search-hl">750</em>`
2. `highlight("a.b", ".")` → 不抛错，正则元字符正确转义
3. `splitOeInput("601, 750 / AXMC;789")` → `["601","750","AXMC","789"]`
4. `splitOeInput("")` → `[]`

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
| 高亮 XSS | 服务端不返回 HTML，前端 `highlight` 用 `replace` 而非 `v-html`，并转义正则元字符；只在 `v-html` 前确保文本本身已由后端控制 |
| `customer_product_id` 旧列名 vs 新列名 | 以现有 ORM 关系为准，不改字段名 |
| 大数据量下 ILIKE 慢 | 候选集 LIMIT 200 + score 截 20；如未来超 10k 行再评估 pg_trgm |

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
- `backend/models/customer_product.py`（加 3 列：`product_name_en`、`product_short_name`、`product_short_name_en`）
- `backend/schemas/customer_product.py`（3 个 schema 加 3 个 Optional 字段）
- `backend/routers/customer_product.py`（**新增** `/search` handler + **新增** `/{product_id}/oes/bulk-sync` handler）
- `frontend/src/api/endpoints.ts`（新增 `PRODUCT_SEARCH.recommend = '/api/customer-products/search'`，`PRODUCT_CUSTOMER.search` 改为转发到该地址并标记 `@deprecated`）
- `frontend/src/components/order/NewOrderDialog.vue`（L223-271 替换为 `<ProductSearchSelect>`；`onProductSelect` 按 §4.2.5 映射回填）
- `frontend/src/components/order/SupplementDialog.vue`（L252 同样替换为 `<ProductSearchSelect>`，复用同一 service + 组件）
- `frontend/src/views/product/ProductManagement.vue`（顶部搜索接入）
- `frontend/src/components/order/ProductEditDialog.vue`
  - L77 / L84 saveField 键修正（`detail_desc` → `product_name` / `detail_desc_en` → `product_name_en`）
  - L109 OE 字段保存改为 `saveOeField` → 调 `bulkSyncOes`
  - 表单初始化（§L804-807）+ 加载时回填（§L1471-1474）补齐 3 个新字段读写
- `docs/spec.md`（在常用接口约定章节补充 `/api/customer-products/search`；移除 `/api/product-customer/search` 条目）

### 删除
- `backend/routers/product_customer.py`（**已删除**，前端零引用；底层 `PrdProductCustomer` 模型仍由其他模块间接使用，**不删除 model/crud/schema**，避免破坏面扩大）

---

## 11. 验收标准

### P0 修复（P0-1 / P0-2 / P0-3 必须全部通过）
- **P0-1 接口路径**: 前端调用 `GET /api/customer-products/search`，后端 200；旧路径 `/api/product-customer/search` 不再被前端引用。
- **P0-2 下单回填**: 选择搜索结果后，`form.customer_code` / `form.customer_model` / `form.oe_number` / `form.unit_price` / `form.product_id` / `form.customer_id` 全部正确回填（即使响应里某些字段为 null 也不报错，UI 给出友好提示）。
- **P0-3 OE 多 token 拆分**: 录入 `601,750,AXMC` 保存后，搜索 `601, 750 / AXMC`（带分隔符的整串）必须返回该条；搜索 `750` 也命中；搜索 `ax`（小写片段）也命中。

### 业务验收
1. alembic 迁移成功，`prd_customer_product` 增加 3 列可空。
2. ProductEditDialog 中英文全称 + 简称 blur 后重新打开仍能看到值（写入正确列）。
3. NewOrderDialog 录入"601,750,AXMC"保存后，搜索"750"返回该条，搜索"601"也返回。
4. 录入产品简称"刹车片"，搜索"刹车"命中，搜索"片"也命中。
5. 录入产品英文名"Brake Pad 750"，搜索"brake"命中（不区分大小写）。
6. 搜索"无此编号"返回 0 条 + `<el-empty>` 占位。
7. 搜索结果红字高亮匹配字段，hover 副图缩略图可预览大图。
8. 客户型号精确匹配排第一（score 100），OE 子串匹配排在其后（score 50）。
9. `match_score` 在前端不展示（仅用于排序）。
10. 后端 pytest 通过（覆盖 4 个名称字段 + 客户型号 + OE + 描述 + 下单回填字段），前端 vitest 通过。
11. `endpoints.ts` 是单一来源，切换搜索接口仅改一处常量。
12. NewOrderDialog 下单流程：选完产品 → 创建订单 → 后端 PI item 写入 customer_code / price_usd / oe 与表单一致。