import client from './client'
import { ORDERS_BFF } from './endpoints'
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
    client.get<PaginatedResponse<Order>>(ORDERS_BFF.list, { params }),

  get: (id: number) =>
    client.get<ApiResponse<OrderDetail>>(ORDERS_BFF.detail(id)),

  create: (data: Partial<Order>) =>
    client.post<ApiResponse<Order>>(ORDERS_BFF.create, data),

  update: (id: number, data: Partial<Order>) =>
    client.put<ApiResponse<Order>>(ORDERS_BFF.update(id), data),

  delete: (id: number) =>
    client.delete<ApiResponse<null>>(ORDERS_BFF.remove(id)),

  importItems: (orderId: number, items: any[]) =>
    client.post<ApiResponse<{ imported: number }>>(
      ORDERS_BFF.importItems(orderId),
      items
    ),

  dashboard: (params: OrderListParams) =>
    client.get<ApiResponse<{
      total_count: number
      total_amount_usd: number
      total_items: number
      status_stats: Record<string, number>
    }>>(ORDERS_BFF.dashboard, { params }),
}
