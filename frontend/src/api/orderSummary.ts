import client from './client'
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

  uploadProductImage: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post<ApiResponse<{ url: string }>>(
      '/api/upload/product-image',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  }
}
