import client from './client'
import type { Order, OrderDetail, ApiResponse, PaginatedResponse } from '@/types/api'

export interface OrderListParams {
  page?: number
  page_size?: number
  search?: string
  customer_id?: number
  status?: string
}

export const orderAPI = {
  list: (params: OrderListParams) =>
    client.get<PaginatedResponse<Order>>('/api/bff/orders', { params }),

  get: (id: number) =>
    client.get<ApiResponse<OrderDetail>>(`/api/bff/orders/${id}`),

  create: (data: Partial<Order>) =>
    client.post<ApiResponse<Order>>('/api/bff/orders', data),

  update: (id: number, data: Partial<Order>) =>
    client.put<ApiResponse<Order>>(`/api/bff/orders/${id}`, data),

  delete: (id: number) =>
    client.delete<ApiResponse<null>>(`/api/bff/orders/${id}`),

  importItems: (orderId: number, items: any[]) =>
    client.post<ApiResponse<{ imported: number }>>(
      `/api/bff/orders/${orderId}/import-items`,
      items
    ),

  dashboard: (params: OrderListParams) =>
    client.get<ApiResponse<{
      total_count: number
      total_amount_usd: number
      total_items: number
      status_stats: Record<string, number>
    }>>('/api/bff/orders/dashboard', { params }),
}
