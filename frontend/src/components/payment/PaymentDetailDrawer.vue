<template>
  <el-drawer
    v-model="visible"
    title="收款详情"
    direction="rtl"
    size="600px"
    @close="onClose"
  >
    <div class="detail-content">
      <!-- 基本信息 -->
      <el-card shadow="never" class="info-card">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="收据号">{{ currentPayment?.receipt_no }}</el-descriptions-item>
          <el-descriptions-item label="PI号">{{ currentPayment?.pi_no }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ currentPayment?.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="付款日期">{{ currentPayment?.payment_date }}</el-descriptions-item>
          <el-descriptions-item label="实收金额">{{ formatAmount(currentPayment?.actual_amount) }}</el-descriptions-item>
          <el-descriptions-item label="手续费">{{ formatAmount(currentPayment?.handling_fee) }}</el-descriptions-item>
          <el-descriptions-item label="付款方式">{{ currentPayment?.payment_method }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ currentPayment?.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 水单图片 -->
      <el-card shadow="never" class="info-card">
        <template #header>
          <span class="card-title">水单图片</span>
        </template>
        <div v-if="currentPayment?.water_image" class="water-image-box">
          <el-image
            :src="currentPayment.water_image"
            :preview-src-list="[currentPayment.water_image]"
            fit="contain"
            class="water-image"
            preview-teleported
          />
          <div class="water-image-actions">
            <el-button size="small" type="primary" @click="triggerReplaceImage">
              <el-icon><Upload /></el-icon>
              替换图片
            </el-button>
          </div>
        </div>
        <el-empty v-else description="暂无水单图片" :image-size="80">
          <el-button size="small" type="primary" @click="triggerReplaceImage">
            <el-icon><Upload /></el-icon>
            上传水单
          </el-button>
        </el-empty>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="onEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="onDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>
  </el-drawer>

  <!-- 隐藏的 file input 用于替换图片 -->
  <input
    ref="fileInputRef"
    type="file"
    accept=".jpg,.jpeg,.png,.pdf"
    style="display: none"
    @change="onFileChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Upload } from '@element-plus/icons-vue'
import type { ArCustomerPayment } from '@/types/payment'
import { apiUrl } from '@/api/base'
import { PAYMENTS } from '@/api/endpoints'

const emit = defineEmits<{
  (e: 'edit', payment: ArCustomerPayment): void
  (e: 'delete', payment: ArCustomerPayment): void
}>()

const visible = ref(false)
const currentPayment = ref<ArCustomerPayment | null>(null)
const fileInputRef = ref<HTMLInputElement>()

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
const MAX_SIZE = 10 * 1024 * 1024 // 10MB

function open(p: ArCustomerPayment) {
  currentPayment.value = { ...p }
  visible.value = true
}

function onClose() {
  currentPayment.value = null
  visible.value = false
}

function formatAmount(amount: number | undefined): string {
  if (amount === undefined || amount === null) return '-'
  return `¥ ${amount.toFixed(2)}`
}

function onEdit() {
  if (currentPayment.value) {
    emit('edit', currentPayment.value)
  }
}

async function onDelete() {
  if (!currentPayment.value) return

  try {
    await ElMessageBox.confirm(
      `确定要删除收据号为 "${currentPayment.value.receipt_no}" 的收款记录吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const response = await fetch(
      apiUrl(PAYMENTS.receivableDetail(currentPayment.value.id)),
      {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      }
    )

    if (!response.ok) {
      throw new Error(`删除失败: ${response.status}`)
    }

    ElMessage.success('删除成功')
    emit('delete', currentPayment.value)
    onClose()
  } catch (error) {
    if (error instanceof Error && error.message !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function triggerReplaceImage() {
  fileInputRef.value?.click()
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length || !currentPayment.value) {
    input.value = ''
    return
  }

  const file = input.files[0]

  // 校验文件类型
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、PDF 格式')
    input.value = ''
    return
  }

  // 校验文件大小
  if (file.size > MAX_SIZE) {
    ElMessage.error('文件大小不能超过 10MB')
    input.value = ''
    return
  }

  // 读取文件为 base64
  const reader = new FileReader()
  reader.onload = async (event) => {
    const base64 = event.target?.result as string

    try {
      const response = await fetch(
        apiUrl(PAYMENTS.receivableDetail(currentPayment.value!.id)),
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ water_image: base64 }),
        }
      )

      if (!response.ok) {
        throw new Error(`更新失败: ${response.status}`)
      }

      // 更新本地数据
      currentPayment.value!.water_image = base64
      ElMessage.success('水单图片更新成功')
    } catch (error) {
      ElMessage.error('水单图片更新失败')
    }
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsDataURL(file)
  input.value = ''
}

defineExpose({ open })
</script>

<style scoped>
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  margin-bottom: 0;
}

.card-title {
  font-weight: 600;
  font-size: 14px;
}

.water-image-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.water-image {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafafa;
}

.water-image-actions {
  display: flex;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.action-buttons .el-button {
  flex: 1;
}
</style>
