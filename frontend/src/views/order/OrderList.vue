<template>
  <div class="order-list-container">
    <div class="toolbar">
      <el-button type="primary" @click="onRefresh">刷新</el-button>
      <el-button @click="onNewOrder">新建订单</el-button>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索订单号/客户名"
        style="width: 240px"
        clearable
        @clear="onSearch"
        @keyup.enter="onSearch"
      />
      <el-button type="primary" @click="onSearch">搜索</el-button>
    </div>

    <el-table
      v-loading="orderStore.loading"
      :data="orderStore.orders"
      stripe
      style="width: 100%"
      @row-click="onRowClick"
    >
      <el-table-column prop="order_no" label="订单号" width="160" />
      <el-table-column prop="customer_name" label="客户" min-width="160" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="item_count" label="产品数" width="80" align="center" />
      <el-table-column prop="pi_count" label="PI数" width="80" align="center" />
      <el-table-column prop="total_amount_usd" label="金额(USD)" width="120" align="right">
        <template #default="{ row }">
          {{ formatAmount(row.total_amount_usd) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="orderStore.pageSize"
        :total="orderStore.total"
        layout="total, prev, pager, next"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOrderStore } from '@/stores/orderStore'
import { format } from 'date-fns'

const router = useRouter()
const orderStore = useOrderStore()
const searchKeyword = ref('')
const currentPage = ref(1)

onMounted(() => {
  orderStore.fetchOrders()
})

function onRefresh() {
  orderStore.fetchOrders()
}

function onSearch() {
  currentPage.value = 1
  orderStore.fetchOrders({ search: searchKeyword.value, page: 1 })
}

function onNewOrder() {
  router.push('/orders/new')
}

function onRowClick(row: any) {
  if (!row || !row.id || isNaN(Number(row.id))) {
    return
  }
  router.push(`/orders/${row.id}`)
}

function onPageChange(p: number) {
  orderStore.setPage(p)
}

function statusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    cancelled: 'danger',
  }
  return map[status] || 'info'
}

function formatAmount(amount: number | undefined) {
  if (amount == null) return '-'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd HH:mm')
  } catch {
    return dateStr
  }
}
</script>

<style scoped>
.order-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  background: #fff;
}
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
