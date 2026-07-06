export const ORDER_STATUS = {
  CANCELLED: 0,
  PENDING: 1,
  PROCESSING: 2,
  COMPLETED: 3,
} as const

export type OrderStatus = typeof ORDER_STATUS[keyof typeof ORDER_STATUS]

export const STATUS_LABEL_MAP: Record<number, string> = {
  0: '已取消',
  1: '待处理',
  2: '处理中',
  3: '已完成',
}

export const STATUS_TAG_TYPE: Record<number, string> = {
  0: 'info',
  1: 'warning',
  2: 'primary',
  3: 'success',
}

export function getStatusLabel(status: number | null | undefined): string {
  if (status === null || status === undefined) return '未知'
  return STATUS_LABEL_MAP[status] || `状态${status}`
}

export function getStatusTagType(status: number | null | undefined): string {
  if (status === null || status === undefined) return 'info'
  return STATUS_TAG_TYPE[status] || 'info'
}
