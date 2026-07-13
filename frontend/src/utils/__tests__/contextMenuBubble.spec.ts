/**
 * 验证：document 上的 contextmenu 监听器会在 row-contextmenu 打开菜单后
 * 立刻把菜单关掉（因为事件会冒泡到 document）。
 */
import { describe, it, expect } from 'vitest'

describe('contextmenu bubble closes menu', () => {
  it('document contextmenu listener closes menu opened by target handler', () => {
    // 模拟 DOM 结构
    document.body.innerHTML = '<div id="row"></div>'
    const row = document.getElementById('row')!

    let menuVisible = false

    // 模拟 onRowContextMenu：在目标上打开菜单
    row.addEventListener('contextmenu', (e) => {
      e.preventDefault()
      menuVisible = true
    })

    // 模拟 onMounted 里的 document 监听器：关闭菜单
    document.addEventListener('contextmenu', () => {
      menuVisible = false
    })

    // 触发右键
    const evt = new MouseEvent('contextmenu', {
      bubbles: true,
      cancelable: true,
      clientX: 100,
      clientY: 100,
    })
    row.dispatchEvent(evt)

    // 期望：菜单最终是关闭的（被 document 监听器关掉）
    expect(menuVisible).toBe(false)
  })

  it('stopPropagation prevents document listener from closing menu', () => {
    document.body.innerHTML = '<div id="row2"></div>'
    const row = document.getElementById('row2')!

    let menuVisible = false

    row.addEventListener('contextmenu', (e) => {
      e.preventDefault()
      e.stopPropagation() // 关键修复
      menuVisible = true
    })

    document.addEventListener('contextmenu', () => {
      menuVisible = false
    })

    const evt = new MouseEvent('contextmenu', {
      bubbles: true,
      cancelable: true,
      clientX: 100,
      clientY: 100,
    })
    row.dispatchEvent(evt)

    expect(menuVisible).toBe(true)
  })
})
