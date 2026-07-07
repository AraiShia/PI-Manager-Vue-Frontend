<template>
  <el-dialog
    v-model="visible"
    title="批量入库"
    width="700px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <div class="batch-info">
      共 {{ items.length }} 个产品待入库
    </div>

    <el-form label-width="80px" class="inspector-form">
      <el-form-item label="验收人">
        <el-input v-model="inspector" placeholder="请输入验收人" />
      </el-form-item>
    </el-form>

    <el-table :data="items" border size="small" max-height="350">
      <el-table-column prop="product_name" label="产品名称" min-width="150" show-overflow-tooltip />
      <el-table-column label="采购数量" width="100" align="right">
        <template #default="{ row }">
          {{ row.quantity }}
        </template>
      </el-table-column>
      <el-table-column label="入库数量" width="140">
        <template #default="{ row, $index }">
          <el-input-number
            v-model="row._inboundQty"
            :min="0"
            :max="row.quantity"
            :precision="0"
            size="small"
            style="width: 100%"
          />
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="onClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">确认入库</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import type { OrderDetailItem } from '@/types/orderSummary'

const emit = defineEmits<{
  success: []
}>()

const visible = ref(false)
const submitting = ref(false)
const items = ref<(OrderDetailItem & { _inboundQty: number })[]>([])
const inspector = ref('')

let piId: number | null = null

function open(orderItems: OrderDetailItem[], orderId: number) {
  visible.value = true
  piId = orderId
  inspector.value = ''

  items.value = orderItems.map((item) => ({
    ...item,
    _inboundQty: item.quantity || 0,
  }))
}

function onClose() {
  visible.value = false
}

async function onSubmit() {
  if (!piId) {
    ElMessage.warning('缺少订单信息')
    return
  }

  // 过滤入库数量为0的项
  const entries = items.value
    .filter((item) => item._inboundQty > 0)
    .map((item) => ({
      pi_item_id: item.id,
      quantity: item._inboundQty,
      remark: '',
    }))

  if (entries.length === 0) {
    ElMessage.warning('请至少输入一个入库数量')
    return
  }

  try {
    submitting.value = true
    const res = await purchaseApi.inboundPiItemsBatch(piId, {
      items: entries,
      inspector: inspector.value,
    })

    if (res.data.code === 200) {
      ElMessage.success('批量入库成功')
      emit('success')
      onClose()
    } else {
      ElMessage.error(res.data.message || '入库失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '入库失败')
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.batch-info {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.inspector-form {
  margin-bottom: 16px;
}
</style>
