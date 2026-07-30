/**
 * @fileoverview 客户回复与往来需求 API 服务模块 (customerReply.ts)
 */
import client from './client'
import { CUSTOMER_REPLIES } from './endpoints'

export interface CustomerReplyItem {
  id: number
  pi_id: number
  customer_id: number
  reply_date: string
  reply_content: string
  reply_type?: 'customer' | 'question' | 'reply' | 'demand' | string
  submitter_name?: string | null
  sequence_num?: number | null
  sequence_label?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CustomerReplyFormPayload {
  pi_id: number
  customer_id?: number
  pi_item_id?: number
  reply_date: string
  reply_content: string
  reply_type?: string
  submitter_name?: string | null
  sequence_num?: number | null
}

export interface CustomerReplyUpdatePayload {
  reply_date?: string
  reply_content?: string
  reply_type?: string
  submitter_name?: string | null
}

export interface CustomerReplyPiListResponse {
  pi_id: number
  pi_no: string
  customer_name: string
  replies: Array<{
    id: number
    reply_type: string
    sequence_label?: string
    submitter_name?: string
    reply_date?: string
    reply_content: string
  }>
}

export const customerReplyApi = {
  /** 获取所有往来回复列表 */
  list: (params: { skip?: number; limit?: number } = {}) =>
    client.get<CustomerReplyItem[]>(CUSTOMER_REPLIES.list, { params }),

  /** 获取某 PI 的所有往来回复列表 */
  getByPi: (piId: number) =>
    client.get<CustomerReplyItem[]>(CUSTOMER_REPLIES.byPi(piId)),

  /** 获取某 PI 带有序号标签的结构化往来列表 */
  getByPiList: (piId: number) =>
    client.get<CustomerReplyPiListResponse>(CUSTOMER_REPLIES.byPiList(piId)),

  /** 获取某 PI 的最新一条回复 */
  getLatestByPi: (piId: number) =>
    client.get<CustomerReplyItem | null>(CUSTOMER_REPLIES.latestByPi(piId)),

  /** 获取某客户的所有往来回复列表 */
  getByCustomer: (customerId: number) =>
    client.get<CustomerReplyItem[]>(CUSTOMER_REPLIES.byCustomer(customerId)),

  /** 新增往来回复记录 */
  create: (payload: CustomerReplyFormPayload) =>
    client.post<CustomerReplyItem>(CUSTOMER_REPLIES.create, payload),

  /** 更新往来回复记录 */
  update: (id: number, payload: CustomerReplyUpdatePayload) =>
    client.put<CustomerReplyItem>(CUSTOMER_REPLIES.update(id), payload),

  /** 删除往来回复记录 */
  remove: (id: number) =>
    client.delete(CUSTOMER_REPLIES.remove(id)),

  /** 导出往来回复记录为 Excel (Blob 文件流) */
  exportExcel: (piId: number, params: { customer_name?: string; start_date?: string; end_date?: string } = {}) =>
    client.post(
      CUSTOMER_REPLIES.export,
      null,
      {
        params: { pi_id: piId, ...params },
        responseType: 'blob',
      }
    ),
}
