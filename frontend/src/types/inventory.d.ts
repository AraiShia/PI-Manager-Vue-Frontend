/** 库存记录（来自 /api/inventory/ 列表接口） */
export interface InventoryItem {
  id: number
  product_id: number
  product_code?: string | null
  oe_number?: string | null
  customer_id: number
  customer_name?: string | null
  supplier_id?: number | null
  supplier_name?: string | null
  pi_id?: number | null
  po_id?: number | null
  total_quantity: number
  shipped_quantity: number
  pending_quantity: number
  purchase_price?: number | null
  current_location?: string | null
  customer_product_code?: string | null
  inventory_customer_price?: number | null
  color?: string | null
  stock_status_color?: string | null
  stock_type: number
  remark?: string | null
  created_at?: string | null
}

/** 库存状态流转请求 */
export interface InventoryTransitionPayload {
  target_status: number
  remark?: string
}

/** 库存状态流转响应 */
export interface InventoryTransitionResponse {
  success: boolean
  data?: {
    id: number
    stock_type: number
    stock_status_color: string
  }
  message?: string
}
