<template>
  <el-dialog
    v-model="visible"
    title="入库"
    width="450px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <el-form label-width="100px">
      <el-form-item label="产品名称">
        <span>{{ item.product_name || '-' }}</span>
      </el-form-item>
      <el-form-item label="采购数量">
        <span>{{ purchaseQuantity }}</span>
      </el-form-item>
      <el-form-item label="入库数量 *" required>
        <el-input-number
          v-model="quantity"
          :min="0"
          :max="purchaseQuantity"
          :precision="0"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="验收人">
        <el-input v-model="inspector" placeholder="请输入验收人" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="remark" placeholder="请输入备注" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="onClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">确定入库</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import type { OrderDetailItem } from '@/types/orderSummary'

const emit = defineEmits<{
  success: []
}>()

const visible = ref(false)
const submitting = ref(false)

const item = ref<Partial<OrderDetailItem>>({})
const quantity = ref(0)
const inspector = ref('')
const remark = ref('')

const purchaseQuantity = computed(() => item.value.quantity || 0)

function open(row: OrderDetailItem) {
  visible.value = true
  item.value = row
  quantity.value = row.quantity || 0
  inspector.value = ''
  remark.value = ''
}

function onClose() {
  visible.value = false
}

async function onSubmit() {
  if (quantity.value <= 0) {
    ElMessage.warning('入库数量必须大于0')
    return
  }

  if (quantity.value > purchaseQuantity.value) {
    ElMessage.warning('入库数量不能大于采购数量')
    return
  }

  try {
    submitting.value = true
    const res = await purchaseApi.inboundPiItem(item.value.id!, {
      quantity: quantity.value,
      inspector: inspector.value,
      remark: remark.value,
    })

    if (res.data.code === 200) {
      ElMessage.success('入库成功')
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
