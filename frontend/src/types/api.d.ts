// API 响应类型

export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

export interface PaginatedData<T> {
  list: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface PaginatedResponse<T = any> extends ApiResponse<PaginatedData<T>> {
  data: PaginatedData<T>
}

export interface Order {
  id: number
  order_no: string
  customer_id: number
  customer_name: string
  status: string
  created_at: string
  total_units?: number
  total_amount_usd?: number
  item_count?: number
  pi_count?: number
}

export interface OrderDetail extends Order {
  items: OrderItem[]
  pi_list: PI[]
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  customer_model: string
  quantity: number
  unit_price_usd: number
  amount_usd: number
}

export interface PI {
  id: number
  pi_no: string
  status: string
  created_at: string
}
