# 收款管理页面实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 新建独立收款管理页面，支持收款列表、添加/编辑/删除、水单上传查看

**架构：** 独立页面路由 `/payments`，左侧列表+右侧滑出详情面板，Dialog 处理添加/编辑，Element Plus 组件

**技术栈：** Vue 3 + TypeScript + Element Plus + Axios

---

## 文件结构

### 新建文件
- `frontend/src/views/payment/PaymentListPage.vue` — 主页面
- `frontend/src/components/payment/PaymentRecordDialog.vue` — 添加/编辑对话框
- `frontend/src/components/payment/PaymentDetailDrawer.vue` — 右侧滑出详情面板
- `frontend/src/components/payment/WaterBillUploader.vue` — 水单上传组件
- `frontend/src/types/payment.ts` — 类型定义

### 修改文件
- `frontend/src/views/order/OrderListPanel.vue` — 添加"收款管理"按钮（已添加）
- `frontend/src/router/index.ts` — 添加 `/payments` 路由

---

## 任务 1：类型定义

**文件：**
- 创建：`frontend/src/types/payment.ts`

- [ ] **步骤 1：创建类型定义文件**

```typescript
// frontend/src/types/payment.ts

export interface ArCustomerPayment {
  id: number
  receipt_no: string        // 收据编号
  pi_id: number             // 关联PI
  customer_id: number       // 关联客户
  amount: number            // 应收金额
  actual_amount: number     // 实收金额
  handling_fee: number       // 手续费
  payment_date: string       // 付款日期
  payment_method: string     // 付款方式
  water_image?: string       // 水单图片(base64)
  remark?: string           // 备注
  // 关联数据
  pi_no?: string            // PI号（冗余展示用）
  customer_name?: string     // 客户名（冗余展示用）
}

export interface PaymentListParams {
  page?: number
  page_size?: number
  keyword?: string           // 搜索：收据号/PI号/客户名
  customer_id?: number
  pi_id?: number
  date_from?: string
  date_to?: string
  status?: string
}

export interface PaymentListResponse {
  list: ArCustomerPayment[]
  total: number
  page: number
  page_size: number
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/types/payment.ts
git commit -m "feat(payment): 添加收款管理类型定义"
```

---

## 任务 2：收款列表页面框架

**文件：**
- 创建：`frontend/src/views/payment/PaymentListPage.vue`

- [ ] **步骤 1：创建页面基础结构**

```vue
<template>
  <div class="payment-list-page">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索收据号/PI号/客户名"
          clearable
          style="width: 240px"
          @keyup.enter="onSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="onDateRangeChange"
        />
        <el-button :icon="Refresh" @click="onRefresh">刷新</el-button>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="onAddPayment">添加收款</el-button>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table
        v-loading="loading"
        :data="list"
        stripe
        border
        height="100%"
        @row-click="onRowClick"
      >
        <el-table-column prop="receipt_no" label="收据号" width="140" />
        <el-table-column prop="pi_no" label="PI号" width="140" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户" min-width="160" show-overflow-tooltip />
        <el-table-column prop="payment_date" label="付款日期" width="120" align="center" />
        <el-table-column prop="actual_amount" label="实收金额" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.actual_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="handling_fee" label="手续费" width="100" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.handling_fee) }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="付款方式" width="100" align="center" />
        <el-table-column prop="water_image" label="水单" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.water_image" type="success" size="small">有</el-tag>
            <el-tag v-else type="info" size="small">无</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="onViewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无收款记录" />
        </template>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="onSizeChange"
        @current-change="onPageChange"
      />
    </div>

    <!-- 子组件 -->
    <PaymentRecordDialog ref="recordDialogRef" @success="onDialogSuccess" />
    <PaymentDetailDrawer ref="detailDrawerRef" @edit="onEditFromDrawer" @delete="onDeleteFromDrawer" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiUrl } from '@/api/base'
import type { ArCustomerPayment, PaymentListParams } from '@/types/payment'
import PaymentRecordDialog from '@/components/payment/PaymentRecordDialog.vue'
import PaymentDetailDrawer from '@/components/payment/PaymentDetailDrawer.vue'

const loading = ref(false)
const list = ref<ArCustomerPayment[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const dateRange = ref<string[] | null>(null)

const recordDialogRef = ref()
const detailDrawerRef = ref()

onMounted(() => {
  fetchList()
})

function formatAmount(amount: number | undefined | null): string {
  if (amount == null || isNaN(amount)) return '-'
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function fetchList() {
  loading.value = true
  try {
    const params: PaymentListParams = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await fetch(apiUrl('/api/payments/receivables?' + new URLSearchParams(params as any).toString()))
    if (res.ok) {
      const data = await res.json()
      list.value = data.list || []
      total.value = data.total || 0
    }
  } catch (e) {
    ElMessage.error('获取收款列表失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

function onRefresh() {
  fetchList()
}

function onDateRangeChange() {
  page.value = 1
  fetchList()
}

function onPageChange(p: number) {
  page.value = p
  fetchList()
}

function onSizeChange(s: number) {
  pageSize.value = s
  page.value = 1
  fetchList()
}

function onRowClick(row: ArCustomerPayment) {
  // 可选：点击行打开详情
}

function onAddPayment() {
  recordDialogRef.value?.open()
}

function onViewDetail(row: ArCustomerPayment) {
  detailDrawerRef.value?.open(row)
}

function onDialogSuccess() {
  fetchList()
}

function onEditFromDrawer(payment: ArCustomerPayment) {
  recordDialogRef.value?.open(payment)
}

async function onDeleteFromDrawer(payment: ArCustomerPayment) {
  // 等待确认后调用 DELETE API
  fetchList()
}
</script>

<style scoped>
.payment-list-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  background: #fff;
  box-sizing: border-box;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.toolbar-left, .toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.table-wrapper {
  flex: 1;
  min-height: 200px;
  overflow: hidden;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/views/payment/PaymentListPage.vue
git commit -m "feat(payment): 创建收款列表页面框架"
```

---

## 任务 3：收款记录 Dialog

**文件：**
- 创建：`frontend/src/components/payment/PaymentRecordDialog.vue`

- [ ] **步骤 1：创建添加/编辑 Dialog**

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑收款' : '添加收款'"
    width="500px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="PI单" prop="pi_id">
        <el-select
          v-model="form.pi_id"
          filterable
          remote
          :remote-method="searchPI"
          placeholder="输入PI号搜索"
          style="width: 100%"
          :loading="piLoading"
        >
          <el-option
            v-for="pi in piOptions"
            :key="pi.id"
            :label="pi.pi_no"
            :value="pi.id"
          >
            <span>{{ pi.pi_no }}</span>
            <span style="color: #999; font-size: 12px; margin-left: 8px;">{{ pi.customer_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="付款日期" prop="payment_date">
        <el-date-picker
          v-model="form.payment_date"
          type="date"
          placeholder="选择日期"
          style="width: 100%"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="实收金额" prop="actual_amount">
        <el-input-number v-model="form.actual_amount" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>

      <el-form-item label="手续费">
        <el-input-number v-model="form.handling_fee" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>

      <el-form-item label="付款方式">
        <el-select v-model="form.payment_method" style="width: 100%">
          <el-option label="银行转账" value="银行转账" />
          <el-option label="现金" value="现金" />
          <el-option label="支票" value="支票" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>

      <el-form-item label="水单图片">
        <WaterBillUploader v-model="form.water_image" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="onClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">确认保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { apiUrl } from '@/api/base'
import type { ArCustomerPayment } from '@/types/payment'
import WaterBillUploader from './WaterBillUploader.vue'

const emit = defineEmits<{ (e: 'success'): void }>()

const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const editingId = ref<number | null>(null)

const form = reactive({
  pi_id: null as number | null,
  payment_date: new Date().toISOString().split('T')[0],
  actual_amount: 0,
  handling_fee: 0,
  payment_method: '银行转账',
  remark: '',
  water_image: '' as string,
})

const rules: FormRules = {
  pi_id: [{ required: true, message: '请选择PI单', trigger: 'change' }],
  payment_date: [{ required: true, message: '请选择付款日期', trigger: 'change' }],
  actual_amount: [{ required: true, message: '请输入实收金额', trigger: 'blur' }],
}

const piLoading = ref(false)
const piOptions = ref<Array<{ id: number; pi_no: string; customer_name: string }>>([])

function open(payment?: ArCustomerPayment) {
  if (payment) {
    isEdit.value = true
    editingId.value = payment.id
    form.pi_id = payment.pi_id
    form.payment_date = payment.payment_date
    form.actual_amount = payment.actual_amount
    form.handling_fee = payment.handling_fee || 0
    form.payment_method = payment.payment_method || '银行转账'
    form.remark = payment.remark || ''
    form.water_image = payment.water_image || ''
    piOptions.value = [{ id: payment.pi_id, pi_no: payment.pi_no || '', customer_name: payment.customer_name || '' }]
  } else {
    isEdit.value = false
    editingId.value = null
    resetForm()
  }
  visible.value = true
}

function resetForm() {
  form.pi_id = null
  form.payment_date = new Date().toISOString().split('T')[0]
  form.actual_amount = 0
  form.handling_fee = 0
  form.payment_method = '银行转账'
  form.remark = ''
  form.water_image = ''
}

async function searchPI(query: string) {
  if (!query || query.length < 1) {
    piOptions.value = []
    return
  }
  piLoading.value = true
  try {
    const res = await fetch(apiUrl(`/api/pi?search=${encodeURIComponent(query)}&page_size=20`))
    if (res.ok) {
      const data = await res.json()
      piOptions.value = (data.list || []).map((pi: any) => ({
        id: pi.id,
        pi_no: pi.pi_no,
        customer_name: pi.customer_name,
      }))
    }
  } catch {
    piOptions.value = []
  } finally {
    piLoading.value = false
  }
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!form.pi_id) {
      ElMessage.warning('请选择PI单')
      return
    }
    submitting.value = true
    try {
      const payload = {
        pi_id: form.pi_id,
        payment_date: form.payment_date,
        actual_amount: form.actual_amount,
        handling_fee: form.handling_fee,
        payment_method: form.payment_method,
        remark: form.remark || undefined,
        water_image: form.water_image || undefined,
      }
      const url = isEdit.value && editingId.value
        ? apiUrl(`/api/payments/receivables/${editingId.value}`)
        : apiUrl('/api/payments/receivables')
      const method = isEdit.value ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        ElMessage.success(isEdit.value ? '编辑成功' : '添加成功')
        emit('success')
        onClose()
      } else {
        const err = await res.json()
        ElMessage.error(err.message || '操作失败')
      }
    } catch {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function onClose() {
  formRef.value?.resetFields()
  resetForm()
  visible.value = false
}

defineExpose({ open })
</script>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/payment/PaymentRecordDialog.vue
git commit -m "feat(payment): 创建收款记录添加/编辑Dialog"
```

---

## 任务 4：水单上传组件

**文件：**
- 创建：`frontend/src/components/payment/WaterBillUploader.vue`

- [ ] **步骤 1：创建 WaterBillUploader 组件**

```vue
<template>
  <div class="water-bill-uploader">
    <!-- 已上传图片预览 -->
    <div v-if="modelValue" class="preview-box">
      <el-image
        :src="imageSrc"
        :preview-src-list="[imageSrc]"
        :preview-teleported="true"
        fit="contain"
        style="width: 200px; height: 150px; border: 1px solid #dcdfe6; border-radius: 4px;"
      />
      <div class="preview-actions">
        <el-button size="small" type="primary" link @click="triggerUpload">替换</el-button>
        <el-button size="small" type="danger" link @click="onRemove">删除</el-button>
      </div>
    </div>

    <!-- 上传区域 -->
    <div v-else class="upload-trigger" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
      <el-icon><Upload /></el-icon>
      <span>点击上传或拖拽水单图片</span>
      <span style="font-size: 12px; color: #999;">支持 jpg/png/pdf</span>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      accept=".jpg,.jpeg,.png,.pdf"
      style="display: none"
      @change="onFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const props = defineProps<{ modelValue?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: string): void }>()

const fileInputRef = ref<HTMLInputElement>()

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) processFile(file)
}

function onDrop(event: DragEvent) {
  const file = event.dataTransfer?.files?.[0]
  if (file) processFile(file)
}

function processFile(file: File) {
  if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
    ElMessage.warning('只支持 jpg/png/pdf 格式')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 10MB')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result as string
    emit('update:modelValue', result)
  }
  reader.readAsDataURL(file)
}

function onRemove() {
  emit('update:modelValue', '')
}

const imageSrc = computed(() => props.modelValue || '')
</script>

<style scoped>
.water-bill-uploader {
  display: inline-block;
}
.preview-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preview-actions {
  display: flex;
  gap: 8px;
}
.upload-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 200px;
  height: 150px;
  border: 2px dashed #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  transition: border-color 0.2s;
}
.upload-trigger:hover {
  border-color: #409eff;
  color: #409eff;
}
</style>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/payment/WaterBillUploader.vue
git commit -m "feat(payment): 创建水单上传组件"
```

---

## 任务 5：收款详情滑出面板

**文件：**
- 创建：`frontend/src/components/payment/PaymentDetailDrawer.vue`

- [ ] **步骤 1：创建 PaymentDetailDrawer 组件**

```vue
<template>
  <el-drawer
    v-model="visible"
    title="收款详情"
    size="600px"
    direction="rtl"
    :with-header="true"
  >
    <div v-if="payment" class="detail-content">
      <!-- 基本信息 -->
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="收据号">{{ payment.receipt_no }}</el-descriptions-item>
        <el-descriptions-item label="PI号">{{ payment.pi_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ payment.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="付款日期">{{ payment.payment_date }}</el-descriptions-item>
        <el-descriptions-item label="实收金额">${{ formatAmount(payment.actual_amount) }}</el-descriptions-item>
        <el-descriptions-item label="手续费">{{ formatAmount(payment.handling_fee) }}</el-descriptions-item>
        <el-descriptions-item label="付款方式">{{ payment.payment_method }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ payment.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 水单图片 -->
      <div class="water-bill-section">
        <div class="section-title">水单图片</div>
        <div v-if="payment.water_image" class="water-bill-preview">
          <el-image
            :src="payment.water_image"
            :preview-src-list="[payment.water_image]"
            :preview-teleported="true"
            fit="contain"
            style="width: 100%; max-height: 400px; border: 1px solid #dcdfe6; border-radius: 4px;"
          />
          <div class="water-bill-actions">
            <el-button size="small" type="primary" link @click="onReplaceImage">替换图片</el-button>
          </div>
        </div>
        <div v-else class="no-water-bill">
          <span>暂无水单图片</span>
          <el-button size="small" type="primary" @click="onUploadWaterBill">上传水单</el-button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="onEdit">编辑</el-button>
        <el-button type="danger" @click="onDelete">删除</el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiUrl } from '@/api/base'
import type { ArCustomerPayment } from '@/types/payment'

const emit = defineEmits<{
  (e: 'edit', payment: ArCustomerPayment): void
  (e: 'delete', payment: ArCustomerPayment): void
}>()

const visible = ref(false)
const payment = ref<ArCustomerPayment | null>(null)

function formatAmount(amount: number | undefined | null): string {
  if (amount == null || isNaN(amount)) return '-'
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function open(p: ArCustomerPayment) {
  payment.value = p
  visible.value = true
}

function onEdit() {
  if (payment.value) {
    emit('edit', payment.value)
    visible.value = false
  }
}

async function onDelete() {
  if (!payment.value) return
  try {
    await ElMessageBox.confirm('确定要删除该收款记录吗？', '确认删除', { type: 'warning' })
    const res = await fetch(apiUrl(`/api/payments/receivables/${payment.value.id}`), { method: 'DELETE' })
    if (res.ok) {
      ElMessage.success('删除成功')
      emit('delete', payment.value)
      visible.value = false
    } else {
      ElMessage.error('删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function onReplaceImage() {
  // 调用文件选择器替换图片
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.jpg,.jpeg,.png,.pdf'
  input.onchange = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file || !payment.value) return
    const reader = new FileReader()
    reader.onload = async (ev) => {
      const base64 = ev.target?.result as string
      try {
        const res = await fetch(apiUrl(`/api/payments/receivables/${payment.value!.id}`), {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ water_image: base64 }),
        })
        if (res.ok) {
          ElMessage.success('水单图片已更新')
          payment.value = { ...payment.value!, water_image: base64 }
        }
      } catch {
        ElMessage.error('更新水单失败')
      }
    }
    reader.readAsDataURL(file)
  }
  input.click()
}

function onUploadWaterBill() {
  onReplaceImage()
}

defineExpose({ open })
</script>

<style scoped>
.detail-content {
  padding: 0 16px;
}
.water-bill-section {
  margin-top: 24px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}
.water-bill-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.water-bill-actions {
  display: flex;
  gap: 8px;
}
.no-water-bill {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 4px;
  color: #909399;
}
.action-buttons {
  margin-top: 32px;
  display: flex;
  gap: 12px;
}
</style>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/payment/PaymentDetailDrawer.vue
git commit -m "feat(payment): 创建收款详情滑出面板"
```

---

## 任务 6：添加路由

**文件：**
- 修改：`frontend/src/router/index.ts`

- [ ] **步骤 1：添加 `/payments` 路由**

在 router/index.ts 的 routes 数组中添加：

```typescript
{
  path: '/payments',
  name: 'PaymentManagement',
  component: () => import('@/views/payment/PaymentListPage.vue'),
},
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "feat(payment): 添加收款管理页面路由"
```

---

## 验收检查清单

- [ ] 类型定义正确，包含所有 ArCustomerPayment 字段
- [ ] PaymentListPage 可通过 `/payments` 路由访问
- [ ] 收款列表正确调用 GET `/api/payments/receivables` API
- [ ] 添加收款 Dialog 支持选择PI/日期/金额/方式/水单上传
- [ ] 编辑收款 Dialog 预填已有数据
- [ ] 水单上传组件支持拖拽上传 jpg/png/pdf
- [ ] 详情面板右侧滑出显示完整收款信息
- [ ] 详情面板支持查看水单大图
- [ ] 编辑/删除功能正确调用后端 API
- [ ] 订单列表页"收款管理"按钮可跳转
