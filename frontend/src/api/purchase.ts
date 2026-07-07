/**
 * 采购相关 API
 */
import client from './client'
import type { ApiResponse } from '@/types/api'

export interface PurchaseItem {
  product_id: number
  pi_item_id?: number
  supplier_id?: number
  product_name?: string
  customer_model?: string
  factory_code?: string
  product_image?: string
  color?: string
  detail_requirement?: string
  link?: string
  quantity: number
  unit_price: number
  labeling_fee?: number
  tax_fee?: number
  shipping_fee?: number
  freight?: number
  remark?: string
}

export interface PurchasePayload {
  dept_id: string
  pi_id: number
  supplier_id?: number
  supplier_name?: string  // 1688店铺名称/微信昵称
  currency?: string
  platform?: string
  items: PurchaseItem[]
  contact_wechat?: string
  link?: string
  screenshot?: string
  remark?: string
  // 线下采购额外字段
  generate_contract?: boolean
  contract_template_id?: number
  supplier_contact?: string
  supplier_phone?: string
  contract_remark?: string
  // 发票
  invoice_path?: string
  invoice_amount?: number
  invoice_currency?: string
}

export interface InboundItem {
  pi_item_id: number
  quantity: number
  remark?: string
}

export const purchaseApi = {
  /**
   * 创建线上采购订单 (1688/微信)
   */
  createOnlinePurchase: (data: PurchasePayload) =>
    client.post<ApiResponse<{ purchase_id: number }>>('/api/purchase-orders/1688', data),

  /**
   * 创建线下采购订单
   */
  createOfflinePurchase: (data: PurchasePayload) =>
    client.post<ApiResponse<{ purchase_id: number }>>('/api/purchase-orders', data),

  /**
   * 获取产品最近采购记录
   */
  getProductLatestPurchase: (productId: number) =>
    client.get<ApiResponse<{ record: any }>>(`/api/purchase-orders/product/${productId}/latest`),

  /**
   * 获取产品最近 1688 链接列表（按 product_id，跨订单）
   */
  getRecent1688Urls: (productId: number, limit: number = 5) =>
    client.get<ApiResponse<{ urls: string[] }>>(
      `/api/purchase-orders/1688/recent-urls?product_id=${productId}&limit=${limit}`
    ),

  /**
   * 更新产品行 1688 链接（同步到 pi_item.shop_url）
   */
  updatePiItemLink: (piItemId: number, link: string) =>
    client.put<ApiResponse<any>>(`/api/pi/items/${piItemId}`, { shop_url: link }),

  /**
   * 单品入库
   */
  inboundPiItem: (itemId: number, data: { quantity: number; inspector?: string; remark?: string }) =>
    client.post<ApiResponse<any>>(`/api/pi/items/${itemId}/inbound`, data),

  /**
   * 批量入库
   */
  inboundPiItemsBatch: (piId: number, data: { items: InboundItem[]; inspector?: string }) =>
    client.post<ApiResponse<any>>(`/api/pi/${piId}/inbound-batch`, data),
}
