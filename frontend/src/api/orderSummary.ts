import client from './client'
import { assetUrl } from './base'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types/api'
import type { 
  OrderListFilter, 
  OrderListParams,
  OrderListResponse,
  OrderDetailResponse,
  OrderDashboardData,
} from '@/types/orderSummary'

export interface OrderItemUpdatePayload {
  [key: string]: any
}

export interface OrderItemUpdateResponse {
  success: boolean
  id: number
  product_id?: number | null
  message?: string
}

export const orderSummaryApi = {
  getOrders: (params: OrderListParams) =>
    client.get<ApiResponse<OrderListResponse>>('/api/bff/orders', { params }),

  getOrderDetail: (orderId: number) =>
    client.get<ApiResponse<OrderDetailResponse>>(`/api/bff/orders/${orderId}/full-detail`),

  getDashboard: (filter?: OrderListFilter) =>
    client.get<ApiResponse<OrderDashboardData>>('/api/bff/orders/dashboard', { params: filter }),

  importItems: (orderId: number, items: any[]) =>
    client.post<ApiResponse<{ imported: number }>>(
      `/api/bff/orders/${orderId}/import-items`,
      items
    ),

  updateOrderItem: (itemId: number, payload: OrderItemUpdatePayload) =>
    client.put<OrderItemUpdateResponse>(
      `/api/pi/items/${itemId}`,
      payload
    ),

  checkFormalRecord: (orderId: number) =>
    client.get<{ exists: boolean }>(`/api/pi/${orderId}/formal-record/exists`),

  saveFormalRecord: (orderId: number) =>
    client.post(`/api/pi/${orderId}/formal-record`),

  uploadProductImage: async (file: File): Promise<AxiosResponse<ApiResponse<{ url: string }>>> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await client.post<ApiResponse<{ url: string }> | { url: string; message?: string }>(
      '/api/images/upload',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    if ('url' in res.data) {
      return {
        ...res,
        data: {
          code: 200,
          data: { url: assetUrl(res.data.url) },
          message: res.data.message || '图片上传成功'
        }
      } as AxiosResponse<ApiResponse<{ url: string }>>
    }

    return res as AxiosResponse<ApiResponse<{ url: string }>>
  }
}
