import client from './client'

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
    client.get<ProductCategory[]>('/api/product-categories/', { params }),
  get: (id: number) =>
    client.get<ProductCategory>(`/api/product-categories/${id}`),
  create: (payload: CategoryFormPayload & { code?: string }, autoCode = true) =>
    client.post<ProductCategory>('/api/product-categories/', payload, { params: { auto_code: autoCode } }),
  update: (id: number, payload: Partial<CategoryFormPayload>) =>
    client.put<ProductCategory>(`/api/product-categories/${id}`, payload),
  remove: (id: number) => client.delete(`/api/product-categories/${id}`),
  nextCode: () => client.get<{ next_code: string }>('/api/product-categories/next-code'),
}