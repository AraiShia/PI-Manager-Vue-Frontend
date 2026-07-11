import client from './client'
import type { ApiResponse } from '@/types/api'
import type {
  Shipment,
  ShipmentDetail,
  ShippableItem,
  ShipmentCreatePayload,
  ShipmentCreateResult,
  ShipmentListParams,
} from '@/types/shipment'

export const shipmentsApi = {
  /** 出货单列表（后端返回数组，无 total） */
  getShipments: (params?: ShipmentListParams) =>
    client.get<Shipment[]>('/api/shipments/', { params }),

  /** 出货单详情（下一轮） */
  getShipment: (id: number) =>
    client.get<ApiResponse<ShipmentDetail>>(`/api/shipments/${id}`),

  /** 获取可出货的产品列表 */
  getShippableItems: (piIds: number[]) =>
    client.get<ApiResponse<ShippableItem[]>>('/api/shipments/shippable-items', {
      params: { pi_ids: piIds.join(',') },
    }),

  /** 从订单创建出货单 */
  createFromOrders: (payload: ShipmentCreatePayload) =>
    client.post<ApiResponse<ShipmentCreateResult>>('/api/shipments/from-orders', payload),

  /** 确认出货单 */
  confirmShipment: (id: number) =>
    client.post<ApiResponse<{ id: number }>>(`/api/shipments/${id}/confirm`),
}
