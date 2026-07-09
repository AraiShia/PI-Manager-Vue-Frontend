// 收款记录
export interface ArCustomerPayment {
  id: number
  receipt_no: string        // 收据编号
  pi_id: number             // 关联PI
  customer_id: number       // 关联客户
  amount: number            // 应收金额
  actual_amount: number      // 实收金额
  handling_fee: number       // 手续费
  payment_date: string       // 付款日期
  payment_method: string      // 付款方式
  water_image?: string      // 水单图片(base64)
  remark?: string           // 备注
  // 关联数据（冗余展示用）
  pi_no?: string
  customer_name?: string
}

// 收款列表查询参数
export interface PaymentListParams {
  page?: number
  page_size?: number
  keyword?: string
  customer_id?: number
  pi_id?: number
  date_from?: string
  date_to?: string
}

// 收款列表响应
export interface PaymentListResponse {
  list: ArCustomerPayment[]
  total: number
  page: number
  page_size: number
}
