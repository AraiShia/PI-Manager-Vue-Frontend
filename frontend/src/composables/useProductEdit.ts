import { ref, computed, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { orderSummaryApi } from '@/api/orderSummary'
import type { OrderDetailItem } from '@/types/orderSummary'

export type FieldStatus = 'idle' | 'saving' | 'success' | 'error'

export interface FieldState {
  status: FieldStatus
  message: string
}

export function useProductEdit(itemRef: Ref<OrderDetailItem | null>) {
  const fieldStates = ref<Record<string, FieldState>>({})
  const dirtyFields = ref<Set<string>>(new Set())

  function setFieldStatus(field: string, status: FieldStatus, message = '') {
    fieldStates.value[field] = { status, message }
  }

  async function saveField(field: string, value: any) {
    const item = itemRef.value
    if (!item) return

    const originalValue = (item as any)[field]
    if (value === originalValue) return

    setFieldStatus(field, 'saving')
    dirtyFields.value.add(field)

    try {
      const res = await orderSummaryApi.updateOrderItem(item.id, { [field]: value })
      if (res.data.code === 200) {
        setFieldStatus(field, 'success', '已保存')
        ;(item as any)[field] = value
        dirtyFields.value.delete(field)
      } else {
        setFieldStatus(field, 'error', res.data.message || '保存失败')
      }
    } catch (e: any) {
      setFieldStatus(field, 'error', e.message || '保存失败')
      ElMessage.error(`${field} 保存失败`)
    }
  }

  const computedTotalAmount = computed(() => {
    const item = itemRef.value
    if (!item) return 0
    const qty = Number(item.quantity || 0)
    const price = Number(item.unit_price || 0)
    return qty * price
  })

  return {
    fieldStates,
    dirtyFields,
    saveField,
    setFieldStatus,
    computedTotalAmount,
  }
}
