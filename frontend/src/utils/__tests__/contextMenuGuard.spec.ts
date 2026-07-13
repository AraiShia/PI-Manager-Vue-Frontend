/**
 * 验证：右键菜单刚打开时，同一次 contextmenu 冒泡触发的 hide 应被忽略。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('context menu open guard', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('ignores hide while justOpened is true, then allows hide after timer', () => {
    let visible = false
    let justOpened = false

    const open = () => {
      visible = true
      justOpened = true
      setTimeout(() => {
        justOpened = false
      }, 0)
    }

    const hide = () => {
      if (justOpened) return
      visible = false
    }

    open()
    // 同一次右键冒泡触发 hide：应被忽略
    hide()
    expect(visible).toBe(true)
    expect(justOpened).toBe(true)

    // 下一 tick 后允许关闭
    vi.runAllTimers()
    hide()
    expect(visible).toBe(false)
  })

  it('keeps selected row available when a menu action closes the menu first', () => {
    const row = { id: 1 }
    let currentRow: typeof row | null = row
    let handledRow: typeof row | null = null

    const hide = () => {
      currentRow = null
    }

    const handleAction = () => {
      const rowBeforeHide = currentRow
      if (!rowBeforeHide) return
      hide()
      handledRow = rowBeforeHide
    }

    handleAction()

    expect(handledRow).toBe(row)
  })
})
