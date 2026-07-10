import { describe, expect, it } from 'vitest'
import { normalizePurchaseFees, pickPurchaseSyncFields } from '../purchaseSync'

describe('purchaseSync utilities', () => {
  it('defaults every fee field to zero when missing or non-finite', () => {
    const result = normalizePurchaseFees()
    expect(result).toEqual({
      purchase_price: 0,
      labeling_fee: 0,
      tax_fee: 0,
      shipping_fee: 0,
      freight: 0,
      total_cost: 0,
    })
  })

  it('treats NaN / null / undefined as zero', () => {
    const result = normalizePurchaseFees({
      purchase_price: null,
      labeling_fee: NaN,
      tax_fee: undefined,
      shipping_fee: 10,
      freight: 5,
    })
    expect(result.purchase_price).toBe(0)
    expect(result.labeling_fee).toBe(0)
    expect(result.tax_fee).toBe(0)
    expect(result.shipping_fee).toBe(10)
    expect(result.freight).toBe(5)
  })

  it('sums total_cost = purchase + labeling + tax + shipping + freight', () => {
    const result = normalizePurchaseFees({
      purchase_price: 100,
      labeling_fee: 2,
      tax_fee: 3,
      shipping_fee: 5,
      freight: 7,
    })
    expect(result.total_cost).toBe(117)
  })

  it('maps freight+shipping into shipping_fee and labeling+tax into misc_fee for PI item', () => {
    const fields = pickPurchaseSyncFields(
      {
        purchase_price: 80,
        labeling_fee: 2,
        tax_fee: 3,
        shipping_fee: 5,
        freight: 7,
        supplier_name: 'Acme',
        shop_url: 'https://example.com',
      },
      'fallback-supplier',
      'fallback-url'
    )
    expect(fields).toEqual({
      purchase_price: 80,
      shipping_fee: 12,
      misc_fee: 5,
      total_order_amount: 97,
      supplier_name: 'Acme',
      shop_url: 'https://example.com',
    })
  })

  it('uses fallback supplier / shop url when source is empty', () => {
    const fields = pickPurchaseSyncFields({}, 'Default Supplier', 'https://default.example')
    expect(fields.supplier_name).toBe('Default Supplier')
    expect(fields.shop_url).toBe('https://default.example')
  })

  it('stringifies supplier_name and shop_url when missing', () => {
    const fields = pickPurchaseSyncFields({})
    expect(fields.supplier_name).toBe('')
    expect(fields.shop_url).toBe('')
  })
})
