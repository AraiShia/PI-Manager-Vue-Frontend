import client from './client'
import { assetUrl } from './base'
import { ORDERS_BFF, PI, PI_ITEMS, IMAGES } from './endpoints'
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
    client.get<ApiResponse<OrderListResponse>>(ORDERS_BFF.list, { params }),

  getOrderDetail: (orderId: number) =>
    client.get<ApiResponse<OrderDetailResponse>>(ORDERS_BFF.fullDetail(orderId)),

  getDashboard: (filter?: OrderListFilter) =>
    client.get<ApiResponse<OrderDashboardData>>(ORDERS_BFF.dashboard, { params: filter }),

  importItems: (orderId: number, items: any[]) =>
    client.post<ApiResponse<{ imported: number }>>(
      ORDERS_BFF.importItems(orderId),
      items
    ),

  updateOrderItem: (itemId: number, payload: OrderItemUpdatePayload) =>
    client.put<OrderItemUpdateResponse>(
      PI_ITEMS.update(itemId),
      payload
    ),

  checkFormalRecord: (orderId: number) =>
    client.get<{ exists: boolean }>(PI.formalRecordExists(orderId)),

  saveFormalRecord: (orderId: number) =>
    client.post(PI.saveFormalRecord(orderId)),

  updatePiStatus: (piId: number, payload: { status: number }) =>
    client.put(PI.status(piId), payload),

  deletePi: (piId: number) =>
    client.delete(PI.remove(piId)),

  uploadProductImage: async (file: File): Promise<AxiosResponse<ApiResponse<{ url: string }>>> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await client.post<ApiResponse<{ url: string }> | { url: string; message?: string }>(
      IMAGES.upload,
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
