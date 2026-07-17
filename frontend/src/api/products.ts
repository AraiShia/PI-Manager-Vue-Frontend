import client from './client'
import { CUSTOMER_PRODUCTS, CUSTOMERS, PRODUCT_CATEGORIES } from './endpoints'

export interface ProductCode {
  id: number
  customer_product_id: number
  product_code: string
  is_primary: boolean
  remark?: string | null
  created_at?: string | null
}

export interface ProductOE {
  id: number
  customer_product_id: number
  oe_number: string
  is_primary: boolean
  remark?: string | null
  created_at?: string | null
}

export interface CustomerProduct {
  id: number
  customer_id: number
  system_code?: string | null
  product_name?: string | null
  customer_model?: string | null
  color?: string | null
  customer_remark?: string | null
  category_id?: string | null
  category_name?: string | null
  price_usd?: number | null
  price_rmb?: number | null
  detail_desc?: string | null
  brand?: string | null
  specifications?: string | null
  image_url?: string | null
  sub_images?: string[] | null
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
  customer_name?: string | null
  code_count?: number
  primary_code?: string | null
  oe_count?: number
  primary_oe?: string | null
  codes?: ProductCode[]
  oes?: ProductOE[]
}

export interface CustomerProductListResponse {
  items: CustomerProduct[]
  total: number
  page: number
  page_size: number
}

export interface ProductFormPayload {
  customer_id: number
  product_name?: string | null
  customer_model?: string | null
  color?: string | null
  customer_remark?: string | null
  category_id?: string | null
  price_usd?: number | null
  price_rmb?: number | null
  detail_desc?: string | null
  brand?: string | null
  specifications?: string | null
  image_url?: string | null
  sub_images?: string[] | null
  codes?: string[] | null
  oes?: string[] | null
  is_active?: boolean
}

export interface CustomerOption {
  id: number
  customer_name?: string | null
  name?: string | null
  customer_code?: string | null
}

export interface CategoryOption {
  id: number
  code?: string | null
  name: string
  parent_id?: string | null
  status?: number | null
}

export const productsApi = {
  list: (params: { page?: number; page_size?: number; search?: string; customer_id?: number; category_code?: string }) =>
    client.get<CustomerProductListResponse>(CUSTOMER_PRODUCTS.list, { params }),
  get: (id: number) => client.get<CustomerProduct>(CUSTOMER_PRODUCTS.detail(id)),
  create: (payload: ProductFormPayload) => client.post<CustomerProduct>(CUSTOMER_PRODUCTS.create, payload),
  update: (id: number, payload: Partial<ProductFormPayload>) => client.put<CustomerProduct>(CUSTOMER_PRODUCTS.update(id), payload),
  remove: (id: number) => client.delete(CUSTOMER_PRODUCTS.remove(id)),
  customers: () => client.get<CustomerOption[]>(CUSTOMERS.list, { params: { limit: 1000 } }),
  categories: () => client.get<CategoryOption[]>(PRODUCT_CATEGORIES.list, { params: { status: 1 } }),
  bulkSyncOes: (id: number, oes: string[]) =>
    client.post(CUSTOMER_PRODUCTS.oesBulkSync(id), { oes }),
}
