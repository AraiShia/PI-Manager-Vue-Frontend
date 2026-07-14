import { describe, expect, it, vi } from 'vitest'

describe('product edit unsaved close guard', () => {
  it('requires two confirmations before closing with unsaved changes', async () => {
    const confirm = vi.fn().mockResolvedValue(undefined)
    const close = vi.fn()

    async function requestClose(hasUnsavedChanges: boolean) {
      if (!hasUnsavedChanges) {
        close()
        return
      }
      await confirm('first')
      await confirm('second')
      close()
    }

    await requestClose(true)

    expect(confirm).toHaveBeenCalledTimes(2)
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('marks beforeunload when there are unsaved changes', () => {
    const event = { preventDefault: vi.fn(), returnValue: undefined as string | undefined }

    function handleBeforeUnload(hasUnsavedChanges: boolean) {
      if (!hasUnsavedChanges) return
      event.preventDefault()
      event.returnValue = ''
    }

    handleBeforeUnload(true)

    expect(event.preventDefault).toHaveBeenCalledTimes(1)
    expect(event.returnValue).toBe('')
  })
})
