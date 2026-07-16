import { describe, expect, it } from 'vitest'
import { PURCHASE } from '../endpoints'
import { normalizePurchaseListPayload, type PurchaseOrderSummary } from '../purchase'

const order: PurchaseOrderSummary = {
  id: 1,
  po_no: 'PO-001',
  pi_id: 2,
  pi_no: 'PI-002',
  supplier_id: 3,
  supplier_name: 'Supplier',
  total_amount: 100,
  currency: 'USD',
  status: 1,
  created_at: '2026-07-16T00:00:00',
}

describe('purchase API compatibility', () => {
  it('uses collection URLs with a trailing slash to avoid proxy redirects', () => {
    expect(PURCHASE.list).toBe('/api/purchase-orders/')
    expect(PURCHASE.createOffline).toBe('/api/purchase-orders/')
  })

  it('normalizes the backend bare-array response', () => {
    expect(normalizePurchaseListPayload([order])).toEqual({ data: [order], total: 1 })
  })

  it('keeps the standard wrapped response shape', () => {
    expect(normalizePurchaseListPayload({ data: { data: [order], total: 8 } })).toEqual({
      data: [order],
      total: 8,
    })
  })
})
