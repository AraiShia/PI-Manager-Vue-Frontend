import { describe, expect, it } from 'vitest'
import {
  LOCKED_COLUMNS,
  applyStoredColumnVisibility,
  enforceLockedColumnsVisible,
  getColumnVisibilityStorageKey,
  isLockedColumn,
  parseStoredColumnVisibility,
  resetColumnVisibilityToDefault,
  serializeColumnVisibility,
  type ColumnOption,
} from '../columnVisibility'

const BASE_OPTIONS: ColumnOption[] = [
  { key: 'order_date', locked: true },
  { key: 'pi_no' },
  { key: 'product_code', locked: true },
  { key: 'oe_number' },
]

describe('columnVisibility utilities', () => {
  it('builds the storage key with order id', () => {
    expect(getColumnVisibilityStorageKey(42)).toBe('order-detail-column-visibility:42')
  })

  it('falls back to a global key when no order id', () => {
    expect(getColumnVisibilityStorageKey()).toBe('order-detail-column-visibility:global')
    expect(getColumnVisibilityStorageKey(null)).toBe('order-detail-column-visibility:global')
    expect(getColumnVisibilityStorageKey('')).toBe('order-detail-column-visibility:')
  })

  it('flags locked columns and exposes the locked list', () => {
    expect(isLockedColumn('product_name')).toBe(true)
    expect(isLockedColumn('pi_no')).toBe(false)
    expect(LOCKED_COLUMNS).toContain('product_name')
  })

  it('returns all-true defaults with locked columns enforced', () => {
    const defaults = resetColumnVisibilityToDefault(BASE_OPTIONS)
    expect(defaults.order_date).toBe(true)
    expect(defaults.product_code).toBe(true)
    expect(defaults.pi_no).toBe(true)
    expect(defaults.oe_number).toBe(true)
  })

  it('forces locked columns to visible when applied over a state', () => {
    const dirty = { order_date: false, pi_no: true, product_code: false, oe_number: false }
    const fixed = enforceLockedColumnsVisible(dirty)
    expect(fixed.order_date).toBe(true)
    expect(fixed.product_code).toBe(true)
    expect(fixed.pi_no).toBe(true)
    expect(fixed.oe_number).toBe(false)
  })

  it('parses stored JSON safely', () => {
    expect(parseStoredColumnVisibility('{"pi_no":false,"oe_number":true}')).toEqual({
      pi_no: false,
      oe_number: true,
    })
    expect(parseStoredColumnVisibility(null)).toEqual({})
    expect(parseStoredColumnVisibility('not json')).toEqual({})
    expect(parseStoredColumnVisibility('[]')).toEqual({})
  })

  it('applies stored values, defaults missing, and enforces locked columns', () => {
    const stored = JSON.stringify({ pi_no: false, oe_number: false })
    const merged = applyStoredColumnVisibility(BASE_OPTIONS, stored)
    expect(merged.order_date).toBe(true)
    expect(merged.product_code).toBe(true)
    expect(merged.pi_no).toBe(false)
    expect(merged.oe_number).toBe(false)
  })

  it('ignores storage entries for unknown columns', () => {
    const stored = JSON.stringify({ pi_no: false, ghost: true })
    const merged = applyStoredColumnVisibility(BASE_OPTIONS, stored)
    expect(merged).not.toHaveProperty('ghost')
    expect(merged.pi_no).toBe(false)
  })

  it('serializes only non-locked columns', () => {
    const state = { order_date: false, pi_no: true, product_code: false, oe_number: false }
    expect(JSON.parse(serializeColumnVisibility(BASE_OPTIONS, state))).toEqual({
      pi_no: true,
      oe_number: false,
    })
  })
})
