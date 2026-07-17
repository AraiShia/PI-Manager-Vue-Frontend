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
 * 复用全局 axios client：
 *  - 自动注入 Authorization Bearer token
 *  - HTTPS 协议升级
 *  - 4xx/5xx 由 client 拦截器统一弹 ElMessage
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
