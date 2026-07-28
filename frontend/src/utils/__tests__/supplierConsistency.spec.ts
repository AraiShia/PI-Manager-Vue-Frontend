import { describe, it, expect } from 'vitest'
import { getItemSupplierName, isSupplierConsistent } from '../supplierConsistency'

describe('supplierConsistency utilities', () => {
  describe('getItemSupplierName', () => {
    it('returns supplier_name if present', () => {
      const item = { supplier_name: ' Supplier A ', factory_name: 'Factory B' }
      expect(getItemSupplierName(item as any)).toBe('Supplier A')
    })

    it('falls back to factory_name if supplier_name is empty', () => {
      const item = { supplier_name: '', factory_name: 'Factory B' }
      expect(getItemSupplierName(item as any)).toBe('Factory B')
    })

    it('falls back to orderSupplierName if both item fields are empty', () => {
      const item = { supplier_name: '', factory_name: '' }
      expect(getItemSupplierName(item as any, 'PI Supplier')).toBe('PI Supplier')
    })
  })

  describe('isSupplierConsistent', () => {
    it('returns true for single item or empty array', () => {
      expect(isSupplierConsistent([])).toBe(true)
      expect(isSupplierConsistent([{ supplier_name: 'Supplier A' }])).toBe(true)
    })

    it('returns true when all items have the same supplier', () => {
      const items = [
        { supplier_name: 'Supplier A' },
        { factory_name: 'Supplier A' },
        { supplier_name: 'Supplier A' },
      ]
      expect(isSupplierConsistent(items as any)).toBe(true)
    })

    it('returns false when items have different suppliers', () => {
      const items = [
        { supplier_name: 'Supplier A' },
        { supplier_name: 'Supplier B' },
      ]
      expect(isSupplierConsistent(items as any)).toBe(false)
    })

    it('returns false when some items have suppliers and others are empty', () => {
      const items = [
        { supplier_name: 'Supplier A' },
        { supplier_name: '' },
      ]
      expect(isSupplierConsistent(items as any)).toBe(false)
    })
  })
})
