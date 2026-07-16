import client from './client'
import { PRODUCT_CATEGORIES } from './endpoints'

export interface ProductCategory {
  id: number
  code: string
  name: string
  parent_id?: string | null
  status?: number | null
  sort_order?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CategoryFormPayload {
  name: string
  parent_id?: string | null
}

export const categoriesApi = {
  list: (params?: { status?: number }) =>
    client.get<ProductCategory[]>(PRODUCT_CATEGORIES.list, { params }),
  get: (id: number) =>
    client.get<ProductCategory>(PRODUCT_CATEGORIES.detail(id)),
  create: (payload: CategoryFormPayload & { code?: string }, autoCode = true) =>
    client.post<ProductCategory>(PRODUCT_CATEGORIES.create, payload, { params: { auto_code: autoCode } }),
  update: (id: number, payload: Partial<CategoryFormPayload>) =>
    client.put<ProductCategory>(PRODUCT_CATEGORIES.update(id), payload),
  remove: (id: number) => client.delete(PRODUCT_CATEGORIES.remove(id)),
  nextCode: () => client.get<{ next_code: string }>(PRODUCT_CATEGORIES.nextCode),
}