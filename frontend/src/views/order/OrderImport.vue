<template>
  <div class="order-import-container">
    <h3>导入订单产品</h3>

    <div class="step-area">
      <el-card>
        <template #header>步骤 1：选择 Excel 文件</template>
        <el-button type="primary" @click="onSelectFile">
          选择 Excel 文件
        </el-button>
        <div v-if="selectedFile" class="file-info">
          已选择：{{ selectedFile }}
        </div>
      </el-card>
    </div>

    <div v-if="previewData.length > 0" class="step-area">
      <el-card>
        <template #header>步骤 2：预览数据（前 5 行）</template>
        <el-table :data="previewData.slice(0, 5)" stripe size="small" max-height="300">
          <el-table-column
            v-for="col in previewColumns"
            :key="col"
            :prop="col"
            :label="col"
            min-width="120"
          />
        </el-table>
        <div class="import-summary">
          共 {{ previewData.length }} 条数据
        </div>
      </el-card>
    </div>

    <div class="actions">
      <el-button @click="onCancel">取消</el-button>
      <el-button
        type="success"
        :disabled="previewData.length === 0"
        :loading="importing"
        @click="onConfirmImport"
      >
        确认导入
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { selectFile, readExcel } from '@/api/nativeBridge'
import { orderAPI } from '@/api/orders'

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.id)

const selectedFile = ref('')
const previewData = ref<any[]>([])
const previewColumns = ref<string[]>([])
const importing = ref(false)

async function onSelectFile() {
  try {
    const filePath = await selectFile('Excel Files (*.xlsx *.xls)')
    if (!filePath) return
    selectedFile.value = filePath

    const data = await readExcel(filePath)
    if (data.length === 0) {
      ElMessage.warning('Excel 文件为空')
      return
    }
    previewData.value = data
    previewColumns.value = Object.keys(data[0])
  } catch (e: any) {
    ElMessage.error('读取文件失败：' + e.message)
  }
}

async function onConfirmImport() {
  if (previewData.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确认导入 ${previewData.value.length} 条产品？`,
      '确认导入',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    importing.value = true
    await orderAPI.importItems(orderId, previewData.value)
    ElMessage.success('导入成功')
    router.push(`/orders/${orderId}`)
  } catch (e: any) {
    ElMessage.error('导入失败：' + (e.message || '未知错误'))
  } finally {
    importing.value = false
  }
}

function onCancel() {
  router.back()
}
</script>

<style scoped>
.order-import-container {
  padding: 20px;
  background: #fff;
  height: 100%;
  overflow: auto;
}
.step-area {
  margin-bottom: 20px;
}
.file-info {
  margin-top: 8px;
  color: #67c23a;
  font-size: 13px;
}
.import-summary {
  margin-top: 10px;
  color: #909399;
  font-size: 13px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
</style>
