/**
 * 订单总表类型定义
 *
 * 包含订单列表、订单详情、筛选条件等相关类型
 * OrderDetailItem 共 41 列，按 A-F 组排列，与 Excel 订单管理总表完全对齐
 */

export interface OrderListItem {
  id: number
  pi_no: string
  customer_id: number
  customer_name: string
  customer_country?: string
  created_at: string
  item_count: number
  total_amount: number
  status: number
  status_label: string
  paid_amount: number
  unpaid_amount: number
  payment_progress: number
  payment_status: string
  stock_remaining: number
  storage_status: string
}

export interface OrderDetailItem {
  id: number
  pi_id: number
  product_id: number | null

  // ========== A组：基础信息 (列1-9) ==========
  order_date: string
  pi_no: string
  product_code: string
  oe_number: string
  remark: string | null
  detail_desc?: string | null
  detail_desc_en?: string | null
  product_name: string
  product_name_en: string | null
  product_short_name: string | null
  product_short_name_en: string | null
  image_url: string | null
  image_url_2: string | null
  customer_model: string | null
  product_feature: string | null
  product_acquires?: string | null
  product_color?: string | null
  category_id?: string | null
  category_name?: string | null
  category_parent_name?: string | null

  // ========== B组：价格财务 (列10-21) ==========
  quantity: number
  unit_price: number
  total_amount: number
  latest_customer_reply: string | null
  customer_prepayment: number
  remaining_payment: number
  estimated_usd_price: number | null
  estimated_margin: number | null
  purchase_price: number
  shipping_fee: number
  misc_fee: number
  labeling_fee?: number
  tax_fee?: number
  freight?: number
  total_cost: number

  // ========== C组：供应商采购 (列22-27) ==========
  factory_name: string | null
  supplier_name?: string | null
  shop_url?: string | null
  delivery_date: string | null
  storage_status: string
  factory_deposit: number | null
  factory_balance: number | null

  // ========== D组：物流入库 (列28-30) ==========
  stock_in_action: string | null
  stock_in_quantity: number
  packaging: string | null               // 包装方式：1件/箱 | 多件/箱 | 1件多箱
  units_per_carton: number | null        // 每箱件数（多件/箱模式）
  cartons_per_unit: number | null        // 每件箱数（1件多箱模式）
  boxes_count: number | null             // 每件箱数别名（1件多箱模式）

  // ========== E组：产品细节 (列31-39) ==========
  purchase_option_name: string | null
  product_detail: string | null
  factory_code: string | null
  carton_size: string | null
  pack_spec: string | null               // 打包规格（自动计算）
  carton_count: number | null
  estimated_volume: number | null        // 预估体积（自动计算）
  carton_gross_weight: number | null
  total_weight: number | null

  // ========== F组：其他属性 (列40-41) ==========
  brand: string | null
  invoice_status: string | null
  invoice_type: string | null
  invoice_rate: string | null

  // ========== 导入预设字段 ==========
  profit_margin: number | null   // 毛利率（%），导入时预设
  exchange_rate: number | null    // 汇率，导入时预设

  // ========== 采购 Dialog 扩展字段（运行时添加） ==========
  labeling_fee?: number
  tax_fee?: number
  freight?: number
  link?: string
  supplier_id?: number
  _total?: number
  _urlOptions?: string[]  // 1688 历史链接下拉选项
}

export interface OrderListFilter {
  search?: string
  status?: number
  customer_id?: number
  date_from?: string
  date_to?: string
}

export interface OrderListParams extends OrderListFilter {
  page: number
  page_size: number
}

export interface OrderListResponse {
  list: OrderListItem[]
  total: number
  page: number
  page_size: number
}

export interface OrderDetailResponse {
  order: OrderListItem
  items: OrderDetailItem[]
}

export interface OrderDashboardData {
  total_count: number
  total_amount: number
  status_stats: Record<string, number>
  payment_stats: {
    total_paid: number
    total_unpaid: number
    payment_rate: number
  }
}

export {}
