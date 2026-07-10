export type FormalRecordAction = 'purchase' | 'repurchase' | 'stockIn'

export const FORMAL_RECORD_REQUIRED_ACTIONS: readonly FormalRecordAction[] = [
  'purchase',
  'repurchase',
  'stockIn',
]

export const FORMAL_ORDER_STATUSES = [2, 3, 4] as const

export function isFormalOrderStatus(status?: number | null): boolean {
  return FORMAL_ORDER_STATUSES.includes(status as 2 | 3 | 4)
}

export function isFormalRecordRequiredAction(action: string): action is FormalRecordAction {
  return (FORMAL_RECORD_REQUIRED_ACTIONS as readonly string[]).includes(action)
}

export function getFormalRecordTooltip(
  hasFormalRecord: boolean,
  isTemporaryPi: boolean
): string {
  if (hasFormalRecord) return '已保存正式PI，可进行采购/入库操作'
  return isTemporaryPi
    ? '临时 PI 需先保存正式纪录后采购/入库'
    : '请先点击「保存正式纪录」锁定PI后再采购/入库'
}

export function detectTemporaryPi(piNo?: string | null): boolean {
  return typeof piNo === 'string' && piNo.endsWith('?')
}
