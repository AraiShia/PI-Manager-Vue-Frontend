<template>
  <el-dialog
    v-model="visible"
    :title="`PI 操作 - ${order?.pi_no || ''}`"
    width="500px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <div class="order-info">
      <div>订单号: <strong>{{ order?.pi_no }}</strong></div>
      <div>客户: {{ order?.customer_name }}</div>
      <div>状态: <el-tag :type="getStatusType(order?.status)">{{ order?.status_label }}</el-tag></div>
    </div>
    
    <el-divider />
    
    <div class="action-buttons">
      <el-button
        v-if="order?.status === 1"
        type="primary"
        size="large"
        style="width: 100%; margin-bottom: 10px"
        @click="onGeneratePi"
      >
        <el-icon><DocumentAdd /></el-icon>
        生成 PI
      </el-button>
      
      <el-button
        v-if="order?.status === 2 || order?.status === 3"
        type="warning"
        size="large"
        style="width: 100%; margin-bottom: 10px"
        @click="onRegeneratePi"
      >
        <el-icon><Refresh /></el-icon>
        重新生成 PI
      </el-button>
      
      <el-button
        type="info"
        size="large"
        style="width: 100%"
        @click="onViewHistory"
      >
        <el-icon><Clock /></el-icon>
        查看历史版本
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, Refresh, Clock } from '@element-plus/icons-vue'
import type { OrderListItem } from '@/types/orderSummary'
import { ORDER_STATUS } from '@/constants/orderStatus'
import { apiUrl } from '@/api/base'
import { PI } from '@/api/endpoints'

const visible = ref(false)
const order = ref<OrderListItem | null>(null)

const emit = defineEmits<{
  (e: 'success'): void
}>()

function getStatusType(status?: number): string {
  switch (status) {
    case ORDER_STATUS.CANCELLED: return 'info'
    case ORDER_STATUS.PENDING: return 'warning'
    case ORDER_STATUS.PROCESSING: return 'primary'
    case ORDER_STATUS.COMPLETED: return 'success'
    default: return 'info'
  }
}

async function onGeneratePi() {
  if (!order.value?.id) return
  try {
    const res = await fetch(apiUrl(PI.generatePi(order.value.id)), {
      method: 'POST'
    })
    if (res.ok) {
      ElMessage.success('PI 生成成功')
      emit('success')
      onClose()
    } else {
      const err = await res.json()
      ElMessage.error(err.message || '生成失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '生成 PI 失败')
  }
}

async function onRegeneratePi() {
  if (!order.value?.id) return
  
  await ElMessageBox.confirm('重新生成 PI 将创建新版本，确定继续?', '确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await fetch(apiUrl(`/api/pi/${order.value!.id}/generate-pi`), {
        method: 'POST'
      })
      if (res.ok) {
        ElMessage.success('PI 重新生成成功')
        emit('success')
        onClose()
      } else {
        const err = await res.json()
        ElMessage.error(err.message || '生成失败')
      }
    } catch (e: any) {
      if (e !== 'cancel') {
        ElMessage.error(e.message || '重新生成 PI 失败')
      }
    }
  }).catch(() => {})
}

function onViewHistory() {
  ElMessage.info('历史版本功能开发中')
}

function onClose() {
  visible.value = false
}

function open(orderData: OrderListItem) {
  order.value = orderData
  visible.value = true
}

defineExpose({ open })
</script>

<style scoped>
.order-info {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
.order-info > div {
  margin-bottom: 8px;
}
.order-info > div:last-child {
  margin-bottom: 0;
}
.action-buttons {
  text-align: center;
}
</style>
