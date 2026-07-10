import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ColumnFilterPanel from '../ColumnFilterPanel.vue'
import type { ColumnOption } from '@/utils/columnVisibility'

const OPTIONS: ColumnOption[] = [
  { key: 'order_date', locked: true, label: '订单日期' },
  { key: 'pi_no', label: 'PI号' },
  { key: 'product_code', locked: true, label: '客户产品编号' },
  { key: 'oe_number', label: 'OE号' },
]

describe('ColumnFilterPanel', () => {
  it('renders the locked label suffix and disables locked checkboxes', () => {
    const wrapper = mount(ColumnFilterPanel, {
      props: {
        options: OPTIONS,
        state: { order_date: true, pi_no: true, product_code: true, oe_number: true },
      },
    })

    const labels = wrapper.findAll('label')
    const lockedLabels = labels.filter((l) => l.text().includes('（锁定）'))
    expect(lockedLabels.length).toBe(2)
    lockedLabels.forEach((label) => {
      const input = label.find('input')
      expect(input.attributes('disabled')).toBeDefined()
    })
  })

  it('emits toggle for non-locked changes', async () => {
    const wrapper = mount(ColumnFilterPanel, {
      props: {
        options: OPTIONS,
        state: { order_date: true, pi_no: true, product_code: true, oe_number: true },
      },
    })

    const labels = wrapper.findAll('label')
    const nonLockedLabel = labels.find((l) => l.text().includes('PI号'))
    const nonLockedInput = nonLockedLabel!.find('input')
    expect(nonLockedInput.attributes('disabled')).toBeUndefined()

    await nonLockedInput.setValue(false)
    expect(wrapper.emitted('toggle')).toBeTruthy()
    const events = wrapper.emitted('toggle') as [string, boolean][]
    expect(events.at(-1)?.[1]).toBe(false)
  })

  it('emits the change event with the column key', async () => {
    const wrapper = mount(ColumnFilterPanel, {
      props: {
        options: OPTIONS,
        state: { pi_no: true, order_date: true, product_code: true, oe_number: true },
      },
    })

    const labels = wrapper.findAll('label')
    const piLabel = labels.find((l) => l.text().includes('PI号'))
    const input = piLabel!.find('input')
    await input.setValue(false)
    const events = wrapper.emitted('toggle') as [string, boolean][]
    expect(events.at(-1)?.[0]).toBe('pi_no')
    expect(events.at(-1)?.[1]).toBe(false)
  })
})
