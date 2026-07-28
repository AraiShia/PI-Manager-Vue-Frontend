import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type {
  OrderListItem,
  OrderDetailItem,
  OrderListFilter,
  OrderListParams,
  OrderDashboardData,
} from '@/types/orderSummary'
import { orderSummaryApi } from '@/api/orderSummary'

export const useOrderSummaryStore = defineStore('orderSummary', () => {
  const viewMode = ref<'list' | 'detail'>('list')
  const orders = ref<OrderListItem[]>([])
  const currentOrder = ref<OrderListItem | null>(null)
  const detailItems = ref<OrderDetailItem[]>([])
  const selectedOrderIds = ref<Set<number>>(new Set())
  const filter = ref<OrderListFilter>({})
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const detailLoading = ref(false)
  const dashboardData = ref<OrderDashboardData | null>(null)

  /** 单据导出与编辑的全局响应式数据状态 */
  const exportDocData = ref<any | null>(null)

  /** 设置单据导出编辑数据，并同步持久化至 sessionStorage */
  function setExportDocData(data: any) {
    exportDocData.value = data
    try {
      if (data) {
        sessionStorage.setItem('export_doc_data', JSON.stringify(data))
      } else {
        sessionStorage.removeItem('export_doc_data')
      }
    } catch (e) {
      console.warn('保存单据编辑数据至 sessionStorage 失败:', e)
    }
  }

  /** 从 sessionStorage 中恢复单据编辑数据 */
  function loadExportDocData(): any | null {
    if (exportDocData.value) return exportDocData.value
    try {
      const cached = sessionStorage.getItem('export_doc_data')
      if (cached) {
        exportDocData.value = JSON.parse(cached)
        return exportDocData.value
      }
    } catch (e) {
      console.warn('从 sessionStorage 加载单据编辑数据失败:', e)
    }
    return null
  }

  const selectedOrders = computed(() => 
    orders.value.filter(o => selectedOrderIds.value.has(o.id))
  )

  const hasSelection = computed(() => selectedOrderIds.value.size > 0)

  async function fetchOrders(newParams?: Partial<OrderListFilter> & { page?: number; page_size?: number }) {
    loading.value = true
    try {
      if (newParams) {
        const { page: p, page_size: ps, ...rest } = newParams
        if (p !== undefined) page.value = p
        if (ps !== undefined) pageSize.value = ps
        if (Object.keys(rest).length > 0) {
          filter.value = { ...filter.value, ...rest }
        }
      }
      const res = await orderSummaryApi.getOrders({
        page: page.value,
        page_size: pageSize.value,
        ...filter.value,
      } as OrderListParams)
      if (res.data.code === 200) {
        orders.value = res.data.data.list
        total.value = res.data.data.total
        page.value = res.data.data.page
        pageSize.value = res.data.data.page_size
      }
    } catch (e) {
      console.error('Failed to fetch orders:', e)
      ElMessage.error('获取订单列表失败')
    } finally {
      loading.value = false
    }
  }

  async function fetchOrderDetail(orderId: number) {
    detailLoading.value = true
    try {
      const res = await orderSummaryApi.getOrderDetail(orderId)
      if (res.data.code === 200) {
        currentOrder.value = res.data.data.order
        detailItems.value = res.data.data.items
        viewMode.value = 'detail'
      }
    } catch (e) {
      console.error('Failed to fetch order detail:', e)
      ElMessage.error('获取订单详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  function setViewMode(mode: 'list' | 'detail') {
    viewMode.value = mode
    if (mode === 'list') {
      fetchOrders()
    }
  }

  function toggleSelect(id: number) {
    const next = new Set(selectedOrderIds.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    selectedOrderIds.value = next
  }

  function clearSelection() {
    selectedOrderIds.value = new Set()
  }

  function setFilter(newFilter: Partial<OrderListFilter>) {
    filter.value = { ...filter.value, ...newFilter }
    page.value = 1
  }

  function resetFilter() {
    filter.value = {}
    page.value = 1
  }

  async function fetchDashboard() {
    try {
      const res = await orderSummaryApi.getDashboard(filter.value)
      if (res.data.code === 200) {
        dashboardData.value = res.data.data
      }
    } catch (e) {
      console.error('Failed to fetch dashboard:', e)
      ElMessage.error('获取仪表盘数据失败')
    }
  }

  return {
    viewMode,
    orders,
    currentOrder,
    detailItems,
    selectedOrderIds,
    filter,
    total,
    page,
    pageSize,
    loading,
    detailLoading,
    dashboardData,
    exportDocData,
    setExportDocData,
    loadExportDocData,
    selectedOrders,
    hasSelection,
    fetchOrders,
    fetchOrderDetail,
    setViewMode,
    toggleSelect,
    clearSelection,
    setFilter,
    resetFilter,
    fetchDashboard,
  }
})
