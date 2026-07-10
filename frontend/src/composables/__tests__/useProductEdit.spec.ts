import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useProductEdit } from '../useProductEdit'
import { orderSummaryApi } from '@/api/orderSummary'

vi.mock('@/api/orderSummary', () => ({
  orderSummaryApi: {
    updateOrderItem: vi.fn().mockResolvedValue({ data: { success: true, id: 1 } }),
  },
}))

function getCalls() {
  return vi.mocked(orderSummaryApi.updateOrderItem).mock.calls
}

function resetCalls() {
  vi.mocked(orderSummaryApi.updateOrderItem).mockClear()
}

describe('useProductEdit', () => {
  it('saves detail_desc and mirrors it to product_name for table display', async () => {
    resetCalls()
    const item = ref<any>({ id: 1, detail_desc: '', product_name: '' })
    const { saveField } = useProductEdit(item)
    await saveField('detail_desc', 'AAA')
    expect(getCalls()[0]).toEqual([1, { detail_desc: 'AAA' }])
    expect(item.value.product_name).toBe('AAA')
  })

  it('saves detail_desc_en and mirrors it to product_name_en', async () => {
    resetCalls()
    const item = ref<any>({ id: 1, detail_desc_en: '', product_name_en: '' })
    const { saveField } = useProductEdit(item)
    await saveField('detail_desc_en', 'English Name')
    expect(getCalls()[0]).toEqual([1, { detail_desc_en: 'English Name' }])
    expect(item.value.product_name_en).toBe('English Name')
  })

  it('does not call API when input stays at "" but original is already null', async () => {
    resetCalls()
    const item = ref<any>({ id: 1, detail_desc_en: null, product_name_en: null })
    const { saveField } = useProductEdit(item)
    await saveField('detail_desc_en', '')
    expect(getCalls()).toHaveLength(0)
  })

  it('uses product_name_en as the original value when saving detail_desc_en', async () => {
    resetCalls()
    const item = ref<any>({
      id: 1,
      detail_desc_en: null,
      product_name_en: 'CCC',
    })
    const { saveField } = useProductEdit(item)
    await saveField('detail_desc_en', 'CCC')
    expect(getCalls()).toHaveLength(0)
    expect(item.value.product_name_en).toBe('CCC')
  })

  it('still saves changed P-Name through the detail_desc_en backend field', async () => {
    resetCalls()
    const item = ref<any>({
      id: 1,
      detail_desc_en: null,
      product_name_en: 'CCC',
    })
    const { saveField } = useProductEdit(item)
    await saveField('detail_desc_en', 'CCCD')
    expect(getCalls()[0]).toEqual([1, { detail_desc_en: 'CCCD' }])
    expect(item.value.product_name_en).toBe('CCCD')
  })

  it('syncs sales total_amount and purchase total_cost separately', async () => {
    resetCalls()
    const item = ref<any>({ id: 1, quantity: 2, unit_price: 10, purchase_price: 5, shipping_fee: 3, misc_fee: 4, total_amount: 0, total_cost: 0 })
    const { saveField } = useProductEdit(item)
    await saveField('unit_price', 12)
    expect(getCalls()[0]).toEqual([1, { unit_price: 12 }])
    expect(item.value.total_amount).toBe(24)
    expect(item.value.total_cost).toBe(0)

    resetCalls()
    await saveField('purchase_price', 6)
    expect(getCalls()[0]).toEqual([1, { purchase_price: 6 }])
    expect(item.value.total_cost).toBe(19)
  })
})
