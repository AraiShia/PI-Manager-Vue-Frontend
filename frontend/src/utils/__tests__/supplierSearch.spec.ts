import { describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}))

import client from '@/api/client'
import { suppliersApi } from '@/api/suppliers'

describe('suppliersApi search', () => {
  it('passes keyword to backend instead of relying on first-page local filtering', () => {
    suppliersApi.list({ skip: 0, limit: 20, keyword: 'ACME' })

    expect(client.get).toHaveBeenCalledWith('/api/suppliers/', {
      params: { skip: 0, limit: 20, keyword: 'ACME' },
    })
  })
})
