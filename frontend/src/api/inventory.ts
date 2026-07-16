import client from './client'
import { INVENTORY } from './endpoints'
import type {
  InventoryItem,
  InventoryTransitionPayload,
  InventoryTransitionResponse,
} from '@/types/inventory'
import type { ApiResponse } from '@/types/api'

export interface InventoryListParams {
  skip?: number
  limit?: number
  product_id?: number
  customer_id?: number
  stock_type?: number
  search?: string
}

export interface InventoryDashboard {
  total_records: number
  total_quantity: number
  in_transit_quantity: number
  pending_inbound_quantity: number
  stocked_quantity: number
}

export interface InboundBatch {
  id: number
  po_id: number
  items: Array<{
    product_id: number
    product_name: string
    quantity: number
    inspector?: string
    inbound_time?: string
    confirmed?: boolean
  }>
  status: number
  created_at: string
}

export const inventoryApi = {
  /** 库存列表（按库存记录维度，非按产品聚合） */
  list: (params?: InventoryListParams) =>
    client.get<InventoryItem[]>(INVENTORY.list, { params }),

  /** 单条库存详情 */
  get: (id: number) =>
    client.get<InventoryItem>(INVENTORY.detail(id)),

  /** 新建库存 */
  create: (payload: Record<string, unknown>) =>
    client.post<{ id: number }>(INVENTORY.create, payload),

  /** 更新库存 */
  update: (id: number, payload: Record<string, unknown>) =>
    client.put<ApiResponse<{ id: number }>>(INVENTORY.update(id), payload),

  /** 删除库存 */
  remove: (id: number) =>
    client.delete(INVENTORY.remove(id)),

  /** 状态流转 */
  transition: (id: number, payload: InventoryTransitionPayload) =>
    client.post<InventoryTransitionResponse>(INVENTORY.transition(id), payload),

  /** 库存仪表盘 */
  dashboard: () =>
    client.get<InventoryDashboard>(INVENTORY.dashboard),

  /** 产品维度的最近变更日志 */
  productLogs: () =>
    client.get<Record<string, unknown>[]>(INVENTORY.productLogs),

  /** 老化分析 */
  aging: (daysThreshold = 60) =>
    client.get<Record<string, unknown>[]>(INVENTORY.aging, {
      params: { days_threshold: daysThreshold },
    }),

  /** 调拨 */
  transfer: (sourceId: number, targetId: number, quantity: number) =>
    client.post(INVENTORY.transfer, {
      source_id: sourceId,
      target_id: targetId,
      quantity,
    }),
}
