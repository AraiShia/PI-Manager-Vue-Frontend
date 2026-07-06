<template>
  <div class="order-detail-container" v-loading="orderStore.loading">
    <div v-if="order" class="detail-content">
      <el-card class="info-card">
        <template #header>订单信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ order.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(order.status)">{{ order.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ order.created_at }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <div class="action-bar">
        <el-button type="primary" @click="onImport">导入产品</el-button>
        <el-button @click="onExport">导出 Excel</el-button>
        <el-button @click="onBack">返回列表</el-button>
      </div>

      <el-card class="items-card">
        <template #header>产品列表</template>
        <el-table :data="order.items" stripe>
          <el-table-column prop="product_name" label="产品名" min-width="160" />
          <el-table-column prop="customer_model" label="客户型号" min-width="120" />
          <el-table-column prop="quantity" label="数量" width="100" align="center" />
          <el-table-column prop="unit_price_usd" label="单价(USD)" width="120" align="right">
            <template #default="{ row }">
              {{ formatCurrency(row.unit_price_usd) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount_usd" label="金额(USD)" width="120" align="right">
            <template #default="{ row }">
              {{ formatCurrency(row.amount_usd) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="order.pi_list?.length" class="pi-card">
        <template #header>PI 列表</template>
        <el-table :data="order.pi_list" stripe>
          <el-table-column prop="pi_no" label="PI号" width="160" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOrderStore } from '@/stores/orderStore'
import { writeExcel, saveFile } from '@/api/nativeBridge'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const orderStore = useOrderStore()
const rawId = route.params.id
const orderId = rawId && !isNaN(Number(rawId)) ? Number(rawId) : 0
const order = computed(() => orderStore.currentOrder)

onMounted(() => {
  if (orderId > 0) {
    orderStore.fetchOrderById(orderId)
  }
})

function onImport() {
  router.push(`/orders/${orderId}/import`)
}

async function onExport() {
  if (!order.value?.items?.length) {
    ElMessage.warning('无产品可导出')
    return
  }
  try {
    const filePath = await saveFile(`${order.value.order_no}_products.xlsx`)
    if (!filePath) return
    const ok = await writeExcel(filePath, order.value.items as any[])
    if (ok) ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error('导出失败：' + e.message)
  }
}

function onBack() {
  router.push('/orders')
}

function statusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info', processing: 'warning', completed: 'success', cancelled: 'danger',
  }
  return map[status] || 'info'
}

function formatCurrency(amount: number | undefined) {
  if (amount == null) return '-'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}
</script>

<style scoped>
.order-detail-container {
  padding: 20px;
  background: #fff;
  height: 100%;
  overflow: auto;
}
.info-card, .items-card, .pi-card {
  margin-bottom: 16px;
}
.action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
</style>
