import client from './client'

export interface ProductSupplierUrl {
  id: number
  product_id: number
  supplier_id: number | null
  supplier_name: string
  url: string
  display_name: string | null
  is_default: boolean
  created_at: string
}

export interface ProductSupplierUrlCreate {
  product_id: number
  supplier_id?: number | null
  supplier_name: string
  url: string
  display_name?: string | null
  is_default?: boolean
}

export interface ProductSupplierUrlUpdate {
  url?: string
  display_name?: string | null
  is_default?: boolean
}

const BASE = '/api/product-supplier-urls'

export const productSupplierUrlsApi = {
  list(
    productId: number,
    supplierId?: number | null,
    supplierName?: string | null,
  ): Promise<ProductSupplierUrl[]> {
    const params = new URLSearchParams({ product_id: String(productId) })
    if (supplierId != null) params.set('supplier_id', String(supplierId))
    if (supplierName) params.set('supplier_name', supplierName)
    return client.get(`${BASE}?${params.toString()}`)
  },

  create(data: ProductSupplierUrlCreate): Promise<ProductSupplierUrl> {
    return client.post(BASE, data)
  },

  update(id: number, data: ProductSupplierUrlUpdate): Promise<ProductSupplierUrl> {
    return client.put(`${BASE}/${id}`, data)
  },

  remove(id: number): Promise<void> {
    return client.delete(`${BASE}/${id}`)
  },
}
