# 产品搜索服务实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现 `GET /api/customer-products/search` 多字段分级搜索 + 前端 `<ProductSearchSelect>` 共享组件，替换 NewOrderDialog/SupplementDialog 现有搜索链。

**架构：** 后端新增 `crud/product_search.py`（候选查询 + Python 精排 + Serializer） + `/search` + `/oes/bulk-sync` 两个路由；前端新增 `productSearch.ts` service + `<ProductSearchSelect>` 组件，供 NewOrderDialog / SupplementDialog / ProductManagement 复用。

**技术栈：** FastAPI + SQLAlchemy + PostgreSQL / 前端 Vue3 + Element Plus + TypeScript + Vitest + Pytest

---

## 文件结构

### 新建
- `backend/crud/product_search.py` — 搜索核心逻辑（候选查询 + 精排 + build_search_item）
- `backend/schemas/product_search.py` — `ProductSearchItem` + `ProductSearchResponse`
- `backend/tests/test_product_search.py` — 27 条 pytest
- `frontend/src/api/productSearch.ts` — productSearchService
- `frontend/src/api/__tests__/productSearch.test.ts` — vitest
- `frontend/src/components/common/ProductSearchSelect.vue` — 搜索下拉组件
- `frontend/src/components/common/__tests__/ProductSearchSelect.test.ts` — 组件测试
- `frontend/src/config/featureFlags.ts` — `USE_PRODUCT_SEARCH: true`

### 修改
- `backend/routers/customer_product.py` — 新增 `/search` handler（必须放在 `/{product_id}` 之前）+ `/oes/bulk-sync`
- `backend/schemas/pi.py` — `PIInvoiceItemCreate` 加 `customer_model`
- `backend/crud/pi.py` — `create_pi_invoice` 写入 `customer_model`
- `frontend/src/api/endpoints.ts` — 加 `PRODUCT_SEARCH.recommend`；`PRODUCT_CUSTOMER.search` 标记 `@deprecated` 并转发
- `frontend/src/components/order/NewOrderDialog.vue` — 替换搜索三件套 + payload 加 `product_id` / `customer_model`
- `frontend/src/components/order/SupplementDialog.vue` — 同上替换
- `frontend/src/views/product/ProductManagement.vue` — 顶部搜索接入

> **不迁移数据库**：名称字段实际存于 `pi_proforma_invoice_item` 表，`prd_customer_product` 结构无需改动。

---

## 后端任务

### 任务 1：后端 Schema — ProductSearchItem + ProductSearchResponse

**文件：** 新建 `backend/schemas/product_search.py`

```python
from typing import Optional
from pydantic import BaseModel


class ProductSearchItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    # 名称/型号
    customer_model: str | None
    product_name: str | None          # 优先 PI item.detail_desc
    product_name_en: str | None
    product_short_name: str | None
    product_short_name_en: str | None
    detail_desc: str | None           # PrdCustomerProduct 独立列
    brand: str | None
    # 下单回填
    customer_code: str | None         # PrdCustomerProductCode.is_primary=true 的 product_code
    product_code: str | None
    price_usd: float | None
    oes: list[str]                   # 主 OE 在前
    image_url: str | None
    sub_images: list[str]
    matched_in: list[str]
    match_score: float


class ProductSearchResponse(BaseModel):
    results: list[ProductSearchItem]
    total: int
```

- [ ] **步骤 1：创建 Schema 文件**

```bash
touch backend/schemas/product_search.py
```

- [ ] **步骤 2：写入上述代码**

- [ ] **Commit**

```bash
git add backend/schemas/product_search.py
git commit -m "feat(schema): add ProductSearchItem + ProductSearchResponse"
```

---

### 任务 2：后端 CRUD — 搜索核心逻辑

**文件：** 新建 `backend/crud/product_search.py`

> 规格原文中的全部实现代码（`split_oe_tokens` / 4 类候选查询 / `latest_pi_item_sq` / `score_product` / `_get_name_fields` / `_build_code` / `_build_oes` / `_parse_sub_images` / `build_search_item` / 主流程）全部照抄进此文件。

- [ ] **步骤 1：创建文件，写入完整实现**

```python
import json
import re
from typing import Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload, selectinload

from models.customer_product import PrdCustomerProduct
from models.customer_product_code import PrdCustomerProductCode
from models.customer_product_oe import PrdCustomerProductOE
from models.customer import CrmCustomer
from models.pi import PiProformaInvoiceItem, PiProformaInvoice
from schemas.product_search import ProductSearchItem, ProductSearchResponse


def split_oe_tokens(keyword: str) -> list[str]:
    """OE 多值拆分：按 [,\s/、;]+ 拆分并去空"""
    return list(filter(None, re.split(r'[,\s/、;]+', keyword)))


def search_products(
    db: Session,
    keyword: str,
    customer_id: int | None = None,
    limit: int = 20,
) -> ProductSearchResponse:
    # === 全文照抄规格 §3.4 + §3.5 + §3.6 的代码实现 ===
    # 1) exact_model_q
    # 2) text_match_q
    # 3) pi_name_match_q（含 detail_desc + customer_model + 3 个简称）
    # 4) oe_match_q
    # 5) candidate_ids 收集
    # 6) P2-2 保护
    # 7) latest_pi_all_sq + 展示用 latest_name_map
    # 8) 最终 products 加载（joinedload/selectinload + deleted_at 过滤）
    # 9) score_product + build_search_item
    # 10) sort + return
    #
    # 关键实现要点（照抄规格）：
    # - latest_pi_item_sq 加 filter(is_deleted == False)
    # - latest_pi_all_sq 加 filter(is_deleted == False)
    # - products query 加 .filter(PrdCustomerProduct.deleted_at.is_(None))
    # - pi_name_match_q 加 PiProformaInvoice.customer_id 过滤
    # - _get_name_fields(): product_name 优先 pi_item.detail_desc
    # - _build_oes(): sorted by not oe.is_primary（主 OE 排前）
    # - _parse_sub_images(): isinstance(item, str) 过滤
    # - build_search_item(): resolved_matched 映射 + customer_name fallback ""
    ...
```

**实现时请严格照抄规格文件中的代码，包括：**
- `split_oe_tokens` 函数
- 4 组候选查询（含 `customer_id` 过滤、`is_deleted == False` 过滤）
- `latest_pi_item_sq` 和 `latest_pi_all_sq` 子查询
- `score_product` + `_get_name_fields` 函数
- `_build_code` / `_build_oes` / `_parse_sub_images` 辅助函数
- `build_search_item` Serializer（含 matched_in 键映射）
- 主流程（排序 → `total` → `[:limit]` → `ProductSearchResponse`）

> 如实现中与规格描述不一致，以规格 `docs/superpowers/specs/2026-07-16-product-search-design.md` 为准。

- [ ] **步骤 2：写一个简单测试验证函数可导入**

```python
# backend/tests/test_product_search.py 临时加一行
from crud.product_search import split_oe_tokens
assert split_oe_tokens("601, 750 / AXMC") == ["601", "750", "AXMC"]
```

```bash
cd backend && python -c "from crud.product_search import split_oe_tokens; print(split_oe_tokens('601, 750 / AXMC'))"
```

预期输出：`['601', '750', 'AXMC']`

- [ ] **Commit**

```bash
git add backend/crud/product_search.py
git commit -m "feat(crud): product search core logic"
```

---

### 任务 3：后端路由 — /search + /oes/bulk-sync

**文件：** 修改 `backend/routers/customer_product.py`

> **关键：必须在 `/{product_id}` 之前定义 `/search` handler！**

- [ ] **步骤 1：在文件顶部 import 新增**

```python
from crud.product_search import search_products
from schemas.product_search import ProductSearchResponse
```

- [ ] **步骤 2：在 `get_customer_product_by_id` 之前添加两个 handler**

```python
@router.get("/search", response_model=ProductSearchResponse)
def search_products_api(
    keyword: str = Query(..., min_length=1, max_length=100),
    customer_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return search_products(db, keyword, customer_id, limit)


@router.post("/{product_id}/oes/bulk-sync")
def bulk_sync_oes(product_id: int, request: BatchImportRequest, db: Session = Depends(get_db)):
    """全替换 OE：先删后增，单事务"""
    from crud.customer_product import batch_add_oes
    # 1. DELETE 全部现有 OE（按 product_id）
    db.query(PrdCustomerProductOE).filter(
        PrdCustomerProductOE.customer_product_id == product_id
    ).delete(synchronize_session=False)
    # 2. BATCH INSERT
    added = batch_add_oes(db, product_id, request.items, request.set_first_as_primary)
    db.commit()
    return {"added": len(added), "removed": 0, "total": len(added)}
```

**注意**：确认 `BatchImportRequest` 已存在且字段为 `items: list[str]` / `set_first_as_primary: bool`。如果不存在，在 `schemas/customer_product.py` 中补加。

- [ ] **步骤 3：确认路由顺序**

在文件中搜索 `/{product_id}`，确认 `/search` 在它上方。如果顺序错了会导致搜索失败。

- [ ] **步骤 4：手动测试**

```bash
curl "http://localhost:8000/api/customer-products/search?keyword=test"
```

预期：返回 JSON（可能为空 `{"results":[],"total":0}`），不报 422。

- [ ] **Commit**

```bash
git add backend/routers/customer_product.py
git commit -m "feat(router): add /search + /oes/bulk-sync, route order fixed"
```

---

### 任务 4：PI Schema + CRUD 扩展

**文件：** 修改 `backend/schemas/pi.py` 和 `backend/crud/pi.py`

- [ ] **步骤 1：在 `PIInvoiceItemCreate` 中加 `customer_model` 字段**

找到 `PIInvoiceItemCreate` 类（大约 Line 13），添加：

```python
customer_model: Optional[str] = None
```

- [ ] **步骤 2：在 `create_pi_invoice` 函数中写入 `customer_model`**

找到构造 `PiProformaInvoiceItem` 的代码，添加：

```python
customer_model=item.customer_model,
```

确保在 `db.add(db_item)` 之前写入。

- [ ] **Commit**

```bash
git add backend/schemas/pi.py backend/crud/pi.py
git commit -m "feat(pi): add customer_model to PIInvoiceItemCreate and create_pi"
```

---

### 任务 5：后端 pytest（27 条）

**文件：** 新建 `backend/tests/test_product_search.py`

逐条照抄规格 §7.1 的 27 条测试用例。每条包含：
- fixture setup（创建 `PrdCustomerProduct` / `PrdCustomerProductOE` / `PiProformaInvoiceItem` 等）
- 调用 `search_products()`
- 断言结果

> **注意**：用 `db.Session()` 或现有 test fixture pattern。确保软删除字段名是 `is_deleted`（PI item）和 `deleted_at`（PrdCustomerProduct），用 `db.flush()` 后立即验证。

- [ ] **Commit**

```bash
git add backend/tests/test_product_search.py
git commit -m "test: 27 pytest cases for product search"
```

---

## 前端任务

### 任务 6：productSearch service + vitest

**文件：** 新建 `frontend/src/api/productSearch.ts`

```typescript
import axios from 'axios'
import type { ProductSearchItem } from './types'

export interface SearchOptions {
  customer_id?: number
  limit?: number
}

export interface ProductSearchResult {
  results: ProductSearchItem[]
  total: number
}

export const productSearchService = {
  controller: null as AbortController | null,

  async search(keyword: string, opts: SearchOptions = {}): Promise<ProductSearchItem[]> {
    // 防抖已在调用方处理
    this.controller?.abort()
    this.controller = new AbortController()
    try {
      const resp = await axios.get<ProductSearchResult>(
        '/api/customer-products/search',
        {
          params: { keyword, customer_id: opts.customer_id, limit: opts.limit ?? 20 },
          signal: this.controller.signal,
        }
      )
      return resp.data.results
    } catch (err) {
      if (axios.isCancel(err)) return []  // 防抖静默忽略
      throw err
    }
  },

  splitOeInput(value: string): string[] {
    return value.split(/[,\s/、;]+/).filter(Boolean)
  },

  splitForHighlight(text: string | null | undefined, keyword: string) {
    if (!text) return []
    if (!keyword) return [{ text, hit: false }]
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return parts.filter(p => p !== '').map(p => ({
      text: p,
      hit: p.toLowerCase() === keyword.toLowerCase(),
    }))
  },
}
```

**类型文件**：确保 `frontend/src/api/types/productSearch.ts` 或在 `productSearch.ts` 同文件底部导出：

```typescript
export interface ProductSearchItem {
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
  oes: string[]
  image_url: string | null
  sub_images: string[]
  matched_in: string[]
  match_score: number
}
```

- [ ] **步骤 2：vitest 测试**

```typescript
// frontend/src/api/__tests__/productSearch.test.ts
import { describe, it, expect } from 'vitest'
import { productSearchService } from '../productSearch'

describe('splitForHighlight', () => {
  it('splits correctly', () => {
    const r = productSearchService.splitForHighlight('刹车片 750', '750')
    expect(r).toEqual([
      { text: '刹车片 ', hit: false },
      { text: '750', hit: true },
    ])
  })
  it('escapes regex chars', () => {
    expect(() => productSearchService.splitForHighlight('a.b', '.')).not.toThrow()
  })
  it('XSS safe', () => {
    const r = productSearchService.splitForHighlight('<script>alert(1)</script>', 'alert')
    // 返回纯文本，不含 <em>
    const html = r.map(s => s.text).join('')
    expect(html).not.toContain('<script>')
  })
})

describe('splitOeInput', () => {
  it('splits tokens', () => {
    expect(productSearchService.splitOeInput('601, 750 / AXMC;789'))
      .toEqual(['601', '750', 'AXMC', '789'])
  })
  it('empty input', () => expect(productSearchService.splitOeInput('')).toEqual([]))
  it('all separators', () => expect(productSearchService.splitOeInput(',,,')).toEqual([]))
})
```

```bash
cd frontend && npx vitest run src/api/__tests__/productSearch.test.ts
```

预期：PASS

- [ ] **Commit**

```bash
git add frontend/src/api/productSearch.ts frontend/src/api/__tests__/productSearch.test.ts
git commit -m "feat(api): productSearchService + vitest"
```

---

### 任务 7：ProductSearchSelect 组件

**文件：** 新建 `frontend/src/components/common/ProductSearchSelect.vue`

- [ ] **步骤 1：实现组件**

组件接收：
```typescript
const props = defineProps<{
  modelValue?: number      // 已选产品 id
  customerId?: number     // 可选：限定客户
  placeholder?: string
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', id: number): void
  (e: 'select', item: ProductSearchItem): void
}>()
```

内部逻辑（参考规格 §4.4）：
1. `el-input` 绑定本地 `keyword`，200ms 防抖后调 `productSearchService.search()`
2. 搜索结果存 `results`，渲染 `<el-select>` 或自定义下拉
3. 每项展示：图片（主图）+ 名称行（中文名/英文名/简称）+ 客户型号 + OE 列表 + 客户名 + 来源标注
4. 命中字段用 `<template v-for>` 分段渲染，`splitForHighlight`，无 `v-html`
5. 选中后 emit `update:modelValue(id)` + `select(item)`

```vue
<template>
  <el-select
    v-model="localSelected"
    filterable
    remote
    :remote-method="handleSearch"
    :loading="loading"
    :placeholder="placeholder || '搜索产品...'"
    style="width: 100%"
    @change="onSelect"
  >
    <el-option
      v-for="item in results"
      :key="item.id"
      :label="formatLabel(item)"
      :value="item.id"
    >
      <!-- 照抄规格 §4.4 的下拉项模板（含 splitForHighlight，无 v-html）-->
    </el-option>
  </el-select>
</template>
```

- [ ] **步骤 2：组件 vitest**

```typescript
// frontend/src/components/common/__tests__/ProductSearchSelect.test.ts
import { mount } from '@vue/test-utils'
import ProductSearchSelect from '../ProductSearchSelect.vue'
import { vi } from 'vitest'

vi.mock('../../api/productSearch', () => ({
  productSearchService: {
    search: vi.fn().mockResolvedValue([{ id: 1, product_name: '刹车片', oes: ['601'], matched_in: ['product_name'] }]),
    splitForHighlight: (text: string) => [{ text, hit: false }],
  },
}))

it('renders search results', async () => {
  const wrapper = mount(ProductSearchSelect, { props: {} })
  await wrapper.vm.handleSearch('刹车')
  expect(wrapper.findAll('.el-option')).toHaveLength(1)
})
```

- [ ] **Commit**

```bash
git add frontend/src/components/common/ProductSearchSelect.vue frontend/src/components/common/__tests__/ProductSearchSelect.test.ts
git commit -m "feat(component): ProductSearchSelect + tests"
```

---

### 任务 8：NewOrderDialog 接入

**文件：** 修改 `frontend/src/components/order/NewOrderDialog.vue`

- [ ] **步骤 1：替换 L223-271**

删除原有的 `searchMode` radio + `el-autocomplete` + `el-select` 三件套（约 50 行），替换为：

```vue
<ProductSearchSelect
  v-model="selectedProductId"
  :customer-id="form.customer_id"
  placeholder="搜索产品..."
  @select="onProductSelect"
/>
```

- [ ] **步骤 2：实现 onProductSelect**

```typescript
import type { ProductSearchItem } from '@/api/types'

const selectedProductId = ref<number | undefined>()
const selectedProduct = ref<ProductSearchItem | null>(null)

function onProductSelect(item: ProductSearchItem) {
  selectedProduct.value = item
  form.customer_id    = item.customer_id
  form.product_id     = item.id           // P0-4
  form.customer_code  = item.customer_code || item.product_code || ''
  form.customer_model = item.customer_model || ''
  form.oe_number      = item.oes[0] || ''   // 主 OE
  form.unit_price     = item.price_usd ?? 0  // USD
  form.detail_desc    = item.detail_desc || item.product_name || ''
}
```

- [ ] **步骤 3：修改下单 payload**

找到 `createOrder` 或 `submit` 函数，在 `items` 数组中添加：

```typescript
items: [{
  product_id: form.product_id ?? null,           // P0-4
  quantity: form.quantity,
  unit_price: form.unit_price,
  customer_code: form.customer_code,
  customer_model: form.customer_model || undefined,
  oe_number: form.oe_number || undefined,
  detail_desc: form.detail_desc || undefined,
}],
```

- [ ] **步骤 4：确认 useProductEdit 的 saveField 链路未动**（规格已确认无需修改）

- [ ] **Commit**

```bash
git add frontend/src/components/order/NewOrderDialog.vue
git commit -m "feat(NewOrderDialog): replace search with ProductSearchSelect, add product_id/customer_model to payload"
```

---

### 任务 9：SupplementDialog 接入

**文件：** 修改 `frontend/src/components/order/SupplementDialog.vue`

与任务 8 相同替换（复用同一组件）。

- [ ] **Commit**

```bash
git add frontend/src/components/order/SupplementDialog.vue
git commit -m "feat(SupplementDialog): replace search with ProductSearchSelect"
```

---

### 任务 10：ProductManagement 顶部搜索接入

**文件：** 修改 `frontend/src/views/product/ProductManagement.vue`

将现有的 `el-input + @change` 替换为 `<ProductSearchSelect>`，选中后导航或回填。

- [ ] **Commit**

```bash
git add frontend/src/views/product/ProductManagement.vue
git commit -m "feat(ProductManagement): integrate ProductSearchSelect"
```

---

### 任务 11：endpoints.ts 常量 + featureFlag

**文件：** 修改 `frontend/src/api/endpoints.ts` + 新建 `frontend/src/config/featureFlags.ts`

- [ ] **步骤 1：endpoints.ts 新增**

```typescript
export const PRODUCT_SEARCH = {
  recommend: '/api/customer-products/search',  // 增强版搜索
} as const

// 原 PRODUCT_CUSTOMER.search 保留但标记废弃
export const PRODUCT_CUSTOMER = {
  ...PRODUCT_CUSTOMER,
  search: PRODUCT_SEARCH.recommend,  // 转发到增强版
} as const
// @deprecated 请在下次重构中删除，只保留 PRODUCT_SEARCH
```

- [ ] **步骤 2：新建 featureFlags.ts**

```typescript
export const FEATURE_FLAGS = {
  USE_PRODUCT_SEARCH: true,  // 切 false 可降级到旧搜索链
} as const
```

- [ ] **Commit**

```bash
git add frontend/src/api/endpoints.ts frontend/src/config/featureFlags.ts
git commit -m "feat(config): add PRODUCT_SEARCH endpoint + USE_PRODUCT_SEARCH flag"
```

---

## 集成与验收

- [ ] **步骤 1：端到端测试**

```bash
# 后端
cd backend && pytest tests/test_product_search.py -v

# 前端
cd frontend && npx vitest run
```

- [ ] **步骤 2：手动验证**

1. 启动后端 `uvicorn backend.main:app --reload`
2. 启动前端 `npm run dev`
3. NewOrderDialog → 输入"刹车片" → 下拉出现结果 → 选中 → 表单字段回填
4. 下单 → 打开 PI → 确认 product_id / customer_model 写入
5. 搜索"601, 750 / AXMC"（带分隔符整串）→ 命中
6. 搜索"750" → 命中；搜索"ax" → 命中（小写）
7. 切换 featureFlag=false → 降级，页面不崩

- [ ] **最终 Commit**

```bash
git add -A && git commit -m "feat: product search service complete, all tests green"
```

---

## 自检清单

对照规格 `docs/superpowers/specs/2026-07-16-product-search-design.md`：

- [ ] P0-1：`/search` 在 `/{product_id}` 之前（FastAPI 路由顺序）
- [ ] P0-2：选搜索结果后 6 个字段全部回填
- [ ] P0-3：`customer_id` 过滤 4 组候选
- [ ] P0-4：`product_id` 入 payload
- [ ] P0-5：`product_name` 优先 `pi_item.detail_desc`
- [ ] P0-6：`pi_name_match_q` 含 `detail_desc` + `customer_model`
- [ ] P0-7：`build_search_item` 返回完整对象，`matched_in` 映射正确
- [ ] P0-8：`PrdCustomerProduct.deleted_at` 过滤
- [ ] P1-3：无 `v-html`，`splitForHighlight` 不返回 HTML
- [ ] P1-4：`/oes/bulk-sync` 单事务，去重，主 OE = 首条
- [ ] P1-8：`latest_pi_item_sq` 加 `is_deleted == False`
- [ ] P2-3：产品加载用 `joinedload`/`selectinload`
- [ ] P2-4：`_build_oes` 按 `is_primary` 排序
- [ ] P1-10：`json.JSONDecodeError` 捕获，`[123]` → `[]`
- [ ] P1-11：非字符串过滤
