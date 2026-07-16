/**
 * 出货管理 (Shipments) 类型定义
 *
 * 对应后端 /api/shipments/* 接口，与旧 PyQt 出货 Tab 保持语义一致。
 */

/** 出货单状态码（与旧 PyQt shipment_tab.STATUS_MAP 对齐） */
export const SHIPMENT_STATUS = {
  PENDING: 1,        // 待出货
  IN_PROGRESS: 2,    // 出货中
  SHIPPED: 3,        // 已出货
  ARRIVED: 4,        // 已到达
} as const

export type ShipmentStatus = (typeof SHIPMENT_STATUS)[keyof typeof SHIPMENT_STATUS] | number

export const SHIPMENT_STATUS_TEXT: Record<number, string> = {
  1: '待出货',
  2: '出货中',
  3: '已出货',
  4: '已到达',
}

export const SHIPMENT_STATUS_COLOR: Record<number, string> = {
  1: '#f59e0b', // 橙色
  2: '#3b82f6', // 蓝色
  3: '#10b981', // 绿色
  4: '#6b7280', // 灰色
}

/** 出货单列表行（与后端 routers/shipment.py serialize_shipment 对齐） */
export interface Shipment {
  id: number
  dept_id?: string | null
  pi_id?: number | null
  pi_no?: string | null
  shipment_no: string
  ci_no?: string | null
  ci_locked?: boolean
  customs_no?: string | null
  pi_nos?: string | null
  total_amount: number
  total_cartons: number
  total_gross_weight?: number
  total_volume?: number
  total_quantity?: number
  payment_status?: number
  status: ShipmentStatus
  stages_count?: number
  created_at?: string | null
}

/** 出货单详情（含 items + stages）。本轮次先不在前端使用，仅预留类型。 */
export interface ShipmentDetail extends Shipment {
  items?: ShipmentDetailItem[]
  stages?: ShipmentStage[]
}

export interface ShipmentDetailItem {
  id: number
  pi_item_id?: number | null
  customer_code?: string
  oe_number?: string
  product_image?: string
  order_quantity: number
  order_unit_price: number
  order_total_amount: number
  cartons_estimated: number
  volume_estimated: number
  gross_weight_kg: number
  shipment_quantity: number
  shipment_unit_price: number
  shipment_total_amount: number
  shipment_cartons: number
  shipment_volume: number
  shipment_weight: number
  remaining_quantity: number
  remaining_cartons: number
  remaining_volume: number
}

export interface ShipmentStage {
  id: number
  shipment_id: number
  stage_name?: string | null
  stage_no: number
  shipment_date?: string | null
  container_no?: string | null
  bl_no?: string | null
  quantity: number
  ci_document?: string | null
  pl_document?: string | null
  storage_location?: string | null
  payment_status: number
  remark?: string | null
}

/** 后端 /api/shipments/shippable-items 返回的可出货明细行 */
export interface ShippableItem {
  pi_item_id: number
  pi_id: number
  pi_no: string
  product_id?: number | null
  product_name: string
  customer_code: string
  customer_name: string
  oe_number: string
  customer_model: string
  product_code: string
  order_quantity: number
  shipped_quantity: number
  remaining_quantity: number
  unit_price: number
  total_amount: number
  pack_spec: string
  carton_gross_weight: number
  carton_length_cm: number
  carton_width_cm: number
  carton_height_cm: number
  product_image?: string | null
}

/** 前端在创建出货单时输入的明细行（POST /api/shipments/from-orders） */
export interface ShipmentCreateItem {
  pi_item_id: number
  product_id?: number | null
  shipment_quantity: number
  unit_price: number
  cartons?: number
  volume_m3?: number
  weight_kg?: number
}

export interface ShipmentCreatePayload {
  dept_id: string
  pi_ids: number[]
  items: ShipmentCreateItem[]
}

export interface ShipmentCreateResult {
  success: boolean
  shipment_id: number
  shipment_no: string
}

/** 列表查询参数 */
export interface ShipmentListParams {
  status?: ShipmentStatus | null
  keyword?: string
  page?: number
  page_size?: number
}
