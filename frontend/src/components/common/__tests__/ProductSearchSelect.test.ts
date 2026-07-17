import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, config } from '@vue/test-utils'
import { nextTick } from 'vue'
import ProductSearchSelect from '../ProductSearchSelect.vue'
import type { CustomerProductSearchItem } from '@/api/customerProduct'

// Stub Element Plus components
config.global.stubs = {
  'el-select': {
    template: '<select class="el-select"><slot /></select>',
    props: ['modelValue', 'placeholder', 'clearable', 'disabled', 'filterable', 'remote', 'loading'],
  },
  'el-option': {
    template: '<option class="el-option"><slot /></option>',
    props: ['label', 'value'],
  },
  'el-image': {
    template: '<img class="el-image" />',
    props: ['src'],
  },
}

// Mock customerProduct API
vi.mock('@/api/customerProduct', () => ({
  splitForHighlight: (text: string | null | undefined, keyword: string) => {
    if (!text || !keyword) return [{ text: text || '', hit: false }]
    const parts = text.split(new RegExp(`(${keyword})`, 'gi'))
    return parts.filter(p => p !== '').map(p => ({
      text: p,
      hit: p.toLowerCase() === keyword.toLowerCase(),
    }))
  },
  searchCustomerProducts: vi.fn(),
}))

const mockResults: CustomerProductSearchItem[] = [
  {
    id: 1,
    customer_id: 1,
    customer_name: 'ACME',
    customer_model: 'ACM-750',
    product_name: '750 刹车片',
    product_name_en: null,
    product_short_name: null,
    product_short_name_en: null,
    detail_desc: null,
    brand: null,
    customer_code: 'C001',
    product_code: null,
    price_usd: 12.5,
    image_url: null,
    sub_images: [],
    oes: ['601', '750'],
    matched_in: ['customer_model'],
    match_score: 100,
  },
]

describe('ProductSearchSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders el-select component', async () => {
    const wrapper = mount(ProductSearchSelect, {
      props: { modelValue: null },
    })
    await nextTick()
    expect(wrapper.find('.el-select').exists()).toBe(true)
  })

  it('renders with selected item', async () => {
    const wrapper = mount(ProductSearchSelect, {
      props: { modelValue: mockResults[0] },
    })
    await nextTick()
    expect(wrapper.find('.el-select').exists()).toBe(true)
  })

  it('renders disabled state', async () => {
    const wrapper = mount(ProductSearchSelect, {
      props: { modelValue: null, disabled: true },
    })
    await nextTick()
    expect(wrapper.find('.el-select').exists()).toBe(true)
  })

  it('renders with custom placeholder', async () => {
    const customPlaceholder = 'Search product'
    const wrapper = mount(ProductSearchSelect, {
      props: { modelValue: null, placeholder: customPlaceholder },
    })
    await nextTick()
    expect(wrapper.find('.el-select').exists()).toBe(true)
  })
})
