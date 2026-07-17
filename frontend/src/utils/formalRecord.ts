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

export interface FormalRecordMissingItem {
  index: number
  name: string
  fields: string[]
}

const FORMAL_RECORD_REQUIRED_FIELDS: ReadonlyArray<{
  key: string
  label: string
  positive?: boolean
}> = [
  { key: 'customer_model', label: '客户型号' },
  { key: 'image_url', label: '主图' },
  { key: 'product_name', label: '产品名称' },
  { key: 'category_id', label: '产品类别' },
  { key: 'quantity', label: '采购数量', positive: true },
  { key: 'unit_price', label: '报价', positive: true },
  { key: 'purchase_price', label: '人民币采购价', positive: true },
  { key: 'product_detail', label: '产品特性' },
  { key: 'supplier_name', label: '供应商' },
  { key: 'carton_length', label: '纸箱长度', positive: true },
  { key: 'carton_width', label: '纸箱宽度', positive: true },
  { key: 'carton_height', label: '纸箱高度', positive: true },
  { key: 'pack_spec', label: '打包规格' },
] as const

function isMissingFormalRecordValue(value: unknown, positive = false): boolean {
  if (value === undefined || value === null || (typeof value === 'string' && value.trim() === '')) {
    return true
  }
  return positive && Number(value) <= 0
}

function parseCartonSize(size: unknown): { length: number; width: number; height: number } {
  const parts = typeof size === 'string'
    ? size.split(/[xX×]/).map((part) => Number.parseFloat(part.trim()))
    : []
  return {
    length: parts[0] || 0,
    width: parts[1] || 0,
    height: parts[2] || 0,
  }
}

/** 返回整单中尚未满足正式记录必填项的商品。 */
export function findFormalRecordMissingItems(
  items: Array<Record<string, unknown>>
): FormalRecordMissingItem[] {
  return items.reduce<FormalRecordMissingItem[]>((missingItems, item, index) => {
    const cartonSize = parseCartonSize(item.carton_size)
    const values: Record<string, unknown> = {
      ...item,
      product_name: item.product_name ?? item.detail_desc,
      supplier_name: item.supplier_name ?? item.factory_name,
      carton_length: item.carton_length ?? cartonSize.length,
      carton_width: item.carton_width ?? cartonSize.width,
      carton_height: item.carton_height ?? cartonSize.height,
    }
    const fields = FORMAL_RECORD_REQUIRED_FIELDS
      .filter((field) => isMissingFormalRecordValue(values[field.key], field.positive ?? false))
      .map((field) => field.label)

    if (fields.length > 0) {
      missingItems.push({
        index: index + 1,
        name: String(item.customer_model || item.product_name || item.product_code || `商品 ${index + 1}`),
        fields,
      })
    }
    return missingItems
  }, [])
}
