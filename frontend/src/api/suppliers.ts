import { reactive } from 'vue'
import client from './client'
import { SUPPLIERS } from './endpoints'

export interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
  dept_id: string
  region?: string | null
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  status: number
  created_at: string
  // 平台分类字段（2026-07-20 新增）
  platform?: '1688' | 'wechat' | 'offline' | null
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface SupplierFormPayload {
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface FindOrCreateSupplierResponse {
  id: number
  supplier_name: string
  supplier_code?: string
  created: boolean  // true=新建，false=复用已有
}

export const suppliersApi = {
  create(payload: SupplierFormPayload) {
    return client.post('/api/suppliers/', payload)
  },
  update(id: number, payload: SupplierFormPayload) {
    return client.put(`/api/suppliers/${id}`, payload)
  },
  delete(id: number) {
    return client.delete(`/api/suppliers/${id}`)
  },
  findOrCreate(payload: SupplierFormPayload & { platform: '1688' | 'wechat' | 'offline' }): Promise<{ data: FindOrCreateSupplierResponse }> {
    return client.post('/api/suppliers/find-or-create', payload)
  },
  list(params?: { skip?: number; limit?: number; keyword?: string }) {
    return client.get('/api/suppliers/', { params })
  },
  getProvinces() {
    return client.get('/api/suppliers/provinces').then((r) => r.data as string[])
  },
  getCities(province: string) {
    return client.get(`/api/suppliers/cities/${province}`).then((r) => r.data as string[])
  },
  // 向后兼容别名
  provinces() {
    return client.get<string[]>(SUPPLIERS.provinces)
  },
  cities(province: string) {
    return client.get<string[]>(SUPPLIERS.cities(province))
  },
  remove(id: number) {
    return client.delete(SUPPLIERS.remove(id))
  },
}

/** 跨组件共享的待采购供应商状态（ProductEditDialog 写入 → PurchaseDialog 读取）*/

export interface PendingSupplier {
  supplier: Supplier | null
  platform: '1688' | 'wechat' | 'offline'
  shop_link: string | null
  wechat_id: string | null
  wechat_nickname: string | null
}

export const pendingSupplierState = reactive<PendingSupplier>({
  supplier: null,
  platform: '1688',
  shop_link: null,
  wechat_id: null,
  wechat_nickname: null,
})