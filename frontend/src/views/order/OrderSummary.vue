<template>
  <div class="order-summary">
    <transition name="fade" mode="out-in">
      <OrderListPanel v-if="store.viewMode === 'list'" key="list" />
      <OrderDetailPanel v-else key="detail" />
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'
import OrderListPanel from './OrderListPanel.vue'
import OrderDetailPanel from './OrderDetailPanel.vue'

const store = useOrderSummaryStore()
const route = useRoute()
const router = useRouter()

onMounted(() => {
  // QWebChannel 初始化已在 main.ts 统一执行，这里不再重复 init()。
  // 业务 store 调用本身不直接依赖 bridge，网络请求通过 client.ts adapter 路由分发。

  if (route.params.id) {
    const id = Number(route.params.id)
    if (!isNaN(id) && id > 0) {
      store.fetchOrderDetail(id)
    } else {
      store.fetchOrders()
    }
  } else {
    store.fetchOrders()
  }
})

watch(() => store.viewMode, (mode) => {
  if (mode === 'list') {
    router.push('/orders')
  } else if (mode === 'detail' && store.currentOrder) {
    router.push(`/orders/${store.currentOrder.id}`)
  }
})
</script>

<style scoped>
.order-summary {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
