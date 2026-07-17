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
  互相冗余，命中字段无高亮，结果不含图片，且 `searchProducts` 实际请求了
  `/api/product-customer/search`（字符串硬编码，未走 `endpoints.ts` 常量）。
- `frontend/src/views/product/ProductManagement.vue` 顶部有独立的产品搜索框，未复用同一搜索服务。
- 后端 `/api/product-customer/search` 实际不存在（mount 在 `/api/product-customers`），
  `backend/crud/product.py` 的 `search_products` 仅基于 `PrdProduct` 单表 ILIKE，
  不识别 `customer_model`、不关联 `PrdCustomerProductOE`。
- 产品 OE 号在 `PrdCustomerProduct.oe_number` 列以字符串存储（已废弃字段），
  现真正使用的是关联表 `PrdCustomerProductOE`（一行一条 OE）。

### 1.2 目标
1. 提供统一、独立、可复用的产品搜索服务，覆盖下单、产品管理、未来模块。
2. 匹配字段包含：**OE 号（关联表）**、**客户型号 customer_model（精确匹配优先）**、
   **产品名称 product_name**、**详细描述 detail_desc**。
3. 保存 OE 号时按逗号/空格/斜杠/分号拆分多条入库，搜索时任一 OE 子串命中即可。
4. 搜索结果展示：图片（主图 + 副图缩略）、匹配字段红字高亮、字段来源标注、客户名。
5. 搜索接口与前端组件完全解耦，便于后续接 ES / pg_trgm 等。

### 1.3 非目标
- 不引入 Elasticsearch / pg_trgm 扩展（YAGNI，未来按需）。
- 不新增 `name_short_cn` / `name_short_en` 字段，靠 `product_name` / `detail_desc` 兜底。
- 不重构 `PrdCustomerProduct.oe_number` 旧字段（已废弃，仅保留兼容）。

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
              │ GET /api/product-customer/   │
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

### 3.1 路由（新增/增强）

**文件**: `backend/routers/product_customer.py`

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
    返回: results (按 score desc, limit 截取) + total
    """
```

### 3.2 Pydantic Schema

**文件**: `backend/schemas/product_search.py`（新建）

```python
class ProductSearchItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_model: str | None
    product_name: str | None
    detail_desc: str | None
    brand: str | None
    image_url: str | None
    sub_images: list[str] = []
    oes: list[str] = []
    matched_in: list[Literal["customer_model", "product_name",
                              "detail_desc", "oe"]] = []
    match_score: float

class ProductSearchResponse(BaseModel):
    results: list[ProductSearchItem]
    total: int
```

### 3.3 CRUD 实现

**文件**: `backend/crud/product_search.py`（新建）

#### 候选集（粗筛，LIMIT 200）
```python
kw = f"%{keyword}%"
candidate_query = (
    db.query(PrdCustomerProduct)
    .outerjoin(PrdCustomerProductOE,
               PrdCustomerProductOE.customer_product_id == PrdCustomerProduct.id)
    .filter(
        PrdCustomerProduct.deleted_at.is_(None),
        or_(
            PrdCustomerProduct.customer_model.ilike(kw),
            PrdCustomerProduct.product_name.ilike(kw),
            PrdCustomerProduct.detail_desc.ilike(kw),
            PrdCustomerProductOE.oe_number.ilike(kw),
        ),
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
def score_product(p: PrdCustomerProduct, kw: str, oe_substrings: set[str]) -> tuple[float, list[str]]:
    score = 0.0
    matched: list[str] = []

    if p.customer_model:
        if p.customer_model == kw:
            score = max(score, 100.0); matched.append("customer_model")
        elif kw.lower() in p.customer_model.lower():
            score = max(score, 80.0); matched.append("customer_model")

    if p.product_name and kw.lower() in p.product_name.lower():
        score = max(score, 60.0); matched.append("product_name")
    if p.detail_desc and kw.lower() in p.detail_desc.lower():
        score = max(score, 40.0); matched.append("detail_desc")

    oes = [oe.oe_number for oe in p.oes if oe.oe_number]
    if any(sub in (oe or "") for oe in oes for sub in oe_substrings):
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
  recommend: '/api/product-customer/search',
} as const
```
并废弃 `PRODUCT_CUSTOMER.search`（迁移 NewOrderDialog 至 `PRODUCT_SEARCH.recommend`）。

---

## 4. 前端设计

### 4.1 productSearchService

**新文件**: `frontend/src/api/productSearch.ts`

```ts
export type MatchField = 'customer_model' | 'product_name'
                      | 'detail_desc' | 'oe'

export interface ProductSearchItem {
  id: number
  customer_id: number
  customer_name: string
  customer_model: string | null
  product_name: string | null
  detail_desc: string | null
  brand: string | null
  image_url: string | null
  sub_images: string[]
  oes: string[]
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

#### 样式
```css
.search-hl { color: #f56c6c; font-weight: 600; }
.ps-thumb { width: 56px; height: 56px; border-radius: 4px; }
.ps-subimg { width: 28px; height: 28px; border-radius: 3px; margin-left: 4px; }
.ps-source { color: #909399; font-size: 12px; margin-left: 8px; }
```

### 4.3 ProductEditDialog OE 字段保存

**文件**: `frontend/src/components/order/ProductEditDialog.vue`
**位置**: `saveField('oe_number', ...)` L102-111

替换逻辑：
```ts
async function saveField(field: string, value: any) {
  if (field === 'oe_number') {
    const list = productSearchService.splitOeInput(value || '')
    await customerProductsApi.bulkSyncOes(productId.value, list)
    return  // 跳过通用 saveField（避免覆盖 PrdCustomerProduct.oe_number 旧字段）
  }
  // ...原逻辑
}
```

**后端依赖**: `POST /api/customer-products/{id}/oes/bulk-sync`
- 接受 `{ oes: ["601", "750", "AXMC"] }`
- 内部先按 `customer_product_id` 删旧，再批量插入新
- 返回 `{ added: number, removed: number, total: number }`

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
GET /api/product-customer/search?keyword=750&limit=20&customer_id=1
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
      "detail_desc": "适用 750 系列，前刹",
      "brand": "ACME",
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
3. **产品名匹配**: 搜 `"刹车片"`，`product_name="750 刹车片"` → score 60，matched_in 含 `product_name`
4. **OE 子串匹配**: 插入 `oes=["601","750","AXMC"]`，搜 `"750"` → score 50，matched_in 含 `oe`
5. **多匹配项排序**: 插入多条 candidate，断言按 score 降序
6. **customer_id 过滤**: 仅返回指定客户产品
7. **keyword 边界**: 空串 → 422；长度 101 → 422

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
- `backend/crud/product_search.py`
- `backend/schemas/product_search.py`
- `backend/tests/test_product_search.py`
- `backend/routers/product_customer.py`（追加 `/search` handler）
- `frontend/src/api/productSearch.ts`
- `frontend/src/api/__tests__/productSearch.test.ts`
- `frontend/src/components/common/ProductSearchSelect.vue`
- `frontend/src/components/common/__tests__/ProductSearchSelect.test.ts`

### 修改
- `frontend/src/api/endpoints.ts`（新增 `PRODUCT_SEARCH`，废弃 `PRODUCT_CUSTOMER.search`）
- `frontend/src/components/order/NewOrderDialog.vue`（L223-271 替换）
- `frontend/src/views/product/ProductManagement.vue`（顶部搜索接入）
- `frontend/src/components/order/ProductEditDialog.vue`（OE 拆分保存 + bulk-sync 调用）
- `backend/routers/customer_product.py`（新增 `bulk_sync_oes` handler）
- `docs/spec.md`（在常用接口约定章节补充 `/api/product-customer/search`）

---

## 11. 验收标准

1. NewOrderDialog 录入"601,750,AXMC"保存后，搜索"750"返回该条，搜索"601"也返回。
2. 搜索"无此编号"返回 0 条 + `<el-empty>` 占位。
3. 搜索结果红字高亮匹配字段，hover 副图缩略图可预览大图。
4. `match_score` 在前端不展示（仅用于排序）。
5. 后端 pytest 7/7 通过，前端 vitest 通过。
6. `endpoints.ts` 是单一来源，切换搜索接口仅改一处常量。