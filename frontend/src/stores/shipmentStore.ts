import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { shipmentsApi } from '@/api/shipments'
import type {
  Shipment,
  ShippableItem,
  ShipmentListParams,
  ShipmentCreatePayload,
  ShipmentCreateResult,
  ShipmentStatus,
} from '@/types/shipment'

export const useShipmentStore = defineStore('shipment', () => {
  // 列表数据
  const list = ref<Shipment[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)

  // 筛选参数
  const statusFilter = ref<ShipmentStatus | null>(null)
  const keyword = ref('')

  // 创建对话框
  const createDialogVisible = ref(false)
  const createLoading = ref(false)

  async function fetchList(params?: Partial<ShipmentListParams>) {
    loading.value = true
    try {
      if (params?.page !== undefined) page.value = params.page
      if (params?.page_size !== undefined) pageSize.value = params.page_size
      if (params?.status !== undefined) statusFilter.value = params.status
      if (params?.keyword !== undefined) keyword.value = params.keyword

      const res = await shipmentsApi.getShipments({
        status: statusFilter.value,
        keyword: keyword.value,
        page: page.value,
        page_size: pageSize.value,
      })
      list.value = res.data ?? []
      total.value = list.value.length
    } catch {
      // 错误已在 client interceptor 处理
    } finally {
      loading.value = false
    }
  }

  async function createFromOrders(payload: ShipmentCreatePayload): Promise<ShipmentCreateResult | null> {
    createLoading.value = true
    try {
      const res = await shipmentsApi.createFromOrders(payload)
      if (res.data.code === 200) {
        ElMessage.success('出货单创建成功')
        createDialogVisible.value = false
        fetchList()
        return res.data.data
      }
      return null
    } catch {
      return null
    } finally {
      createLoading.value = false
    }
  }

  function openCreateDialog() {
    createDialogVisible.value = true
  }

  function closeCreateDialog() {
    createDialogVisible.value = false
  }

  return {
    list,
    total,
    page,
    pageSize,
    loading,
    statusFilter,
    keyword,
    createDialogVisible,
    createLoading,
    fetchList,
    createFromOrders,
    openCreateDialog,
    closeCreateDialog,
  }
})
