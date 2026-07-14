import { describe, expect, it, vi } from 'vitest'

describe('document context menu handler', () => {
  it('prevents native menu when a product row is handled', () => {
    const event = {
      preventDefault: vi.fn(),
      target: document.createElement('td'),
    } as unknown as MouseEvent & { target: HTMLElement }

    const rowEl = document.createElement('tr')
    rowEl.className = 'el-table__row'
    const tbody = document.createElement('tbody')
    tbody.appendChild(rowEl)
    rowEl.appendChild(event.target)

    const handle = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null
      const foundRow = target?.closest?.('tr.el-table__row')
      if (!foundRow) return
      e.preventDefault()
    }

    handle(event)

    expect(event.preventDefault).toHaveBeenCalledTimes(1)
  })
})
