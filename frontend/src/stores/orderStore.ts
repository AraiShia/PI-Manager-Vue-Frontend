import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { orderAPI } from '@/api/orders'
import type { Order, OrderDetail } from '@/types/api'
import type { OrderListParams } from '@/api/orders'

export const useOrderStore = defineStore('order', () => {
  const orders = ref<Order[]>([])
  const currentOrder = ref<OrderDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const params = ref<OrderListParams>({})

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  async function fetchOrders(newParams?: OrderListParams) {
    loading.value = true
    if (newParams) {
      params.value = newParams
      page.value = newParams.page || 1
      pageSize.value = newParams.page_size || 20
    }
    try {
      const res: any = await orderAPI.list({ page: page.value, page_size: pageSize.value, ...params.value })
      const data = res.data || res
      orders.value = data.list || []
      total.value = data.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchOrderById(id: number) {
    loading.value = true
    try {
      const res: any = await orderAPI.get(id)
      currentOrder.value = res.data || res
    } finally {
      loading.value = false
    }
  }

  function setPage(p: number) {
    page.value = p
    fetchOrders({ ...params.value, page: p })
  }

  return { orders, currentOrder, total, page, pageSize, totalPages, loading, fetchOrders, fetchOrderById, setPage }
})
