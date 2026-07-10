import { describe, expect, it } from 'vitest'
import {
  FORMAL_RECORD_REQUIRED_ACTIONS,
  detectTemporaryPi,
  getFormalRecordTooltip,
  isFormalOrderStatus,
  isFormalRecordRequiredAction,
} from '../formalRecord'

describe('formalRecord utilities', () => {
  it('detects temporary PI by trailing "?"', () => {
    expect(detectTemporaryPi('PISM2207061000?')).toBe(true)
    expect(detectTemporaryPi('PISM2207061000')).toBe(false)
    expect(detectTemporaryPi('')).toBe(false)
    expect(detectTemporaryPi(null)).toBe(false)
    expect(detectTemporaryPi(undefined)).toBe(false)
  })

  it('flags purchase / repurchase / stockIn as formal-record-gated', () => {
    expect(FORMAL_RECORD_REQUIRED_ACTIONS).toEqual(['purchase', 'repurchase', 'stockIn'])
    expect(isFormalRecordRequiredAction('purchase')).toBe(true)
    expect(isFormalRecordRequiredAction('repurchase')).toBe(true)
    expect(isFormalRecordRequiredAction('stockIn')).toBe(true)
    expect(isFormalRecordRequiredAction('edit')).toBe(false)
    expect(isFormalRecordRequiredAction('delete')).toBe(false)
  })

  it('treats confirmed and later lifecycle statuses as formal', () => {
    expect(isFormalOrderStatus(0)).toBe(false)
    expect(isFormalOrderStatus(1)).toBe(false)
    expect(isFormalOrderStatus(2)).toBe(true)
    expect(isFormalOrderStatus(3)).toBe(true)
    expect(isFormalOrderStatus(4)).toBe(true)
  })

  it('returns "saved" tooltip when formal record exists', () => {
    expect(getFormalRecordTooltip(true, false)).toBe('已保存正式PI，可进行采购/入库操作')
    expect(getFormalRecordTooltip(true, true)).toBe('已保存正式PI，可进行采购/入库操作')
  })

  it('returns temporary-specific tooltip for "?" PI without formal record', () => {
    expect(getFormalRecordTooltip(false, true)).toBe('临时 PI 需先保存正式纪录后采购/入库')
  })

  it('returns generic tooltip when no formal record and not temporary', () => {
    expect(getFormalRecordTooltip(false, false)).toBe('请先点击「保存正式纪录」锁定PI后再采购/入库')
  })
})
