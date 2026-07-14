import client from './client'

export interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  status?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface SupplierFormPayload {
  supplier_code: string
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
}

export const suppliersApi = {
  list: (params: { skip?: number; limit?: number; keyword?: string } = {}) =>
    client.get<Supplier[]>('/api/suppliers/', { params }),
  get: (id: number) => client.get<Supplier>(`/api/suppliers/${id}`),
  create: (payload: SupplierFormPayload, deptId = 'S') =>
    client.post<Supplier>('/api/suppliers/', payload, { params: { dept_id: deptId } }),
  update: (id: number, payload: Partial<SupplierFormPayload>) =>
    client.put<Supplier>(`/api/suppliers/${id}`, payload),
  remove: (id: number) => client.delete(`/api/suppliers/${id}`),
  provinces: () => client.get<string[]>('/api/suppliers/provinces'),
  cities: (province: string) => client.get<string[]>(`/api/suppliers/cities/${encodeURIComponent(province)}`),
}