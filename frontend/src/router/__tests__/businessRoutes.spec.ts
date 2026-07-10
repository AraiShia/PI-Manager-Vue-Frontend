import { describe, expect, it } from 'vitest'
import { BUSINESS_ROUTES } from '../businessRoutes'

const expectedKeys = [
  'products', 'customers', 'suppliers', 'quotes', 'pi', 'purchase',
  'shipment', 'customer_payment', 'supplier_payment', 'inventory',
  'order_summary',
]

describe('BUSINESS_ROUTES', () => {
  it('covers every PyQt business menu', () => {
    expect(BUSINESS_ROUTES.map(item => item.key)).toEqual(expectedKeys)
  })

  it('uses stable absolute paths', () => {
    expect(BUSINESS_ROUTES.every(item => item.path.startsWith('/'))).toBe(true)
    expect(BUSINESS_ROUTES.find(item => item.key === 'shipment')?.path).toBe('/shipments')
    expect(BUSINESS_ROUTES.find(item => item.key === 'customer_payment')?.path).toBe('/payments/customer')
  })

  it('marks currently implemented modules', () => {
    const implemented = BUSINESS_ROUTES.filter(item => item.implemented).map(item => item.key)
    expect(implemented).toEqual(['shipment', 'customer_payment', 'order_summary'])
  })

  it('provides display metadata for every placeholder module', () => {
    for (const route of BUSINESS_ROUTES.filter(item => !item.implemented)) {
      expect(route.title.trim()).not.toBe('')
      expect(route.source.trim()).not.toBe('')
      expect(route.owner.trim()).not.toBe('')
    }
  })
})
