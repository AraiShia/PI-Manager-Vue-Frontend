import client from './client'
import { SUPPLIERS } from './endpoints'

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
  list: (params: { skip?: number; limit?: number; keyword?: string; signal?: AbortSignal } = {}) => {
    const { signal, ...rest } = params
    return client.get<Supplier[]>(SUPPLIERS.list, { params: rest, signal })
  },
  get: (id: number) => client.get<Supplier>(SUPPLIERS.detail(id)),
  create: (payload: SupplierFormPayload, deptId = 'S') =>
    client.post<Supplier>(SUPPLIERS.create, payload, { params: { dept_id: deptId } }),
  update: (id: number, payload: Partial<SupplierFormPayload>) =>
    client.put<Supplier>(SUPPLIERS.update(id), payload),
  remove: (id: number) => client.delete(SUPPLIERS.remove(id)),
  provinces: () => client.get<string[]>(SUPPLIERS.provinces),
  cities: (province: string) => client.get<string[]>(SUPPLIERS.cities(province)),
}