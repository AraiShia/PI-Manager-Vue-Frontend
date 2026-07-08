

export interface ColumnOption {
  key: string
  label?: string
  locked?: boolean
}

export interface ColumnVisibilityState {
  [key: string]: boolean
}

const COLUMN_VISIBILITY_STORAGE_KEY_PREFIX = 'order-detail-column-visibility'

export const LOCKED_COLUMNS: readonly string[] = [
  'order_date',
  'product_code',
  'product_name',
  'image_url',
  'quantity',
  'unit_price',
  'total_amount',
  'purchase_price',
  'shipping_fee',
  'misc_fee',
  'total_cost',
  'factory_name',
  'estimated_volume',
  'invoice_status',
]

export function getColumnVisibilityStorageKey(orderId?: number | string | null): string {
  return orderId == null
    ? `${COLUMN_VISIBILITY_STORAGE_KEY_PREFIX}:global`
    : `${COLUMN_VISIBILITY_STORAGE_KEY_PREFIX}:${orderId}`
}

export function isLockedColumn(key: string): boolean {
  return LOCKED_COLUMNS.includes(key)
}

export function resetColumnVisibilityToDefault(
  options: ReadonlyArray<ColumnOption>
): ColumnVisibilityState {
  const result: ColumnVisibilityState = {}
  for (const option of options) {
    result[option.key] = true
  }
  for (const key of LOCKED_COLUMNS) {
    result[key] = true
  }
  return result
}

export function enforceLockedColumnsVisible(
  state: ColumnVisibilityState
): ColumnVisibilityState {
  const next: ColumnVisibilityState = { ...state }
  for (const key of LOCKED_COLUMNS) {
    next[key] = true
  }
  return next
}

export function parseStoredColumnVisibility(raw: string | null): ColumnVisibilityState {
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      const out: ColumnVisibilityState = {}
      for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
        if (typeof v === 'boolean') out[k] = v
      }
      return out
    }
  } catch {
    /* ignore */
  }
  return {}
}

export function applyStoredColumnVisibility(
  options: ReadonlyArray<ColumnOption>,
  raw: string | null
): ColumnVisibilityState {
  const defaults = resetColumnVisibilityToDefault(options)
  const stored = parseStoredColumnVisibility(raw)
  for (const option of options) {
    if (option.locked) {
      defaults[option.key] = true
    } else if (typeof stored[option.key] === 'boolean') {
      defaults[option.key] = stored[option.key]
    }
  }
  return enforceLockedColumnsVisible(defaults)
}

export function serializeColumnVisibility(
  options: ReadonlyArray<ColumnOption>,
  state: ColumnVisibilityState
): string {
  const payload: ColumnVisibilityState = {}
  for (const option of options) {
    if (!option.locked && typeof state[option.key] === 'boolean') {
      payload[option.key] = state[option.key]
    }
  }
  return JSON.stringify(payload)
}
