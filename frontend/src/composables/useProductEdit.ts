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

  function isBlank(value: any): boolean {
    return value === '' || value === null || value === undefined
  }

  async function saveField(field: string, value: any) {
    const item = itemRef.value
    if (!item) return

    const displayField = field === 'detail_desc' ? 'product_name' : field === 'detail_desc_en' ? 'product_name_en' : field
    const originalValue = (item as any)[displayField] ?? (item as any)[field]
    const originalBlank = isBlank(originalValue)
    const nextBlank = isBlank(value)
    if (nextBlank && originalBlank) return
    if (nextBlank === false && originalValue === value) return

    setFieldStatus(field, 'saving')
    dirtyFields.value.add(field)

    try {
      const res = await orderSummaryApi.updateOrderItem(item.id, { [field]: value })
      if (res.data.success === true) {
        setFieldStatus(field, 'success', '已保存')
        ;(item as any)[field] = value
        if (field === 'detail_desc') {
          ;(item as any).product_name = value
        }
        if (field === 'detail_desc_en') {
          ;(item as any).product_name_en = value
        }
        if (field === 'quantity' || field === 'unit_price') {
          ;(item as any).total_amount = Number((item as any).quantity || 0) * Number((item as any).unit_price || 0)
        }
        if (field === 'quantity' || field === 'purchase_price' || field === 'shipping_fee' || field === 'misc_fee') {
          ;(item as any).total_cost = Number((item as any).purchase_price || 0) * Number((item as any).quantity || 0) + Number((item as any).shipping_fee || 0) + Number((item as any).misc_fee || 0)
        }
        if (field === 'supplier_name') {
          ;(item as any).factory_name = value
        }
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
