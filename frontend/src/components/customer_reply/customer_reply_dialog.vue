<template>
  <el-dialog
    v-model="dialogVisible"
    title="客户往来需求与回复记录管理"
    width="860px"
    destroy-on-close
    append-to-body
    class="customer-reply-dialog"
    @open="handleOpen"
  >
    <!-- 头部信息卡片 -->
    <div class="dialog-header-info mb-4">
      <div class="header-info-left">
        <el-tag type="primary" effect="light" class="info-tag me-2">
          PI 单号: {{ piNo || piId || '未绑定' }}
        </el-tag>
        <el-tag type="success" effect="light" class="info-tag">
          客户名称: {{ customerName || '通用客户' }}
        </el-tag>
      </div>
      <div class="header-info-right">
        <el-button
          type="primary"
          :icon="Plus"
          size="small"
          @click="showAddForm"
        >
          新增沟通需求
        </el-button>
        <el-button
          type="success"
          plain
          :icon="Download"
          size="small"
          :loading="exporting"
          @click="handleExport"
        >
          导出 Excel
        </el-button>
        <el-button
          type="info"
          plain
          :icon="Refresh"
          size="small"
          :loading="loading"
          @click="fetchReplies"
        >
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选与搜索工具栏 -->
    <div class="filter-toolbar mb-3">
      <el-row :gutter="12" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索回复内容或提交人..."
            clearable
            size="small"
            :prefix-icon="Search"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filterType"
            placeholder="回复类型"
            clearable
            size="small"
            style="width: 100%"
          >
            <el-option label="全部类型" value="" />
            <el-option label="客户回复 (customer)" value="customer" />
            <el-option label="客户提问 (question)" value="question" />
            <el-option label="我方答复 (reply)" value="reply" />
            <el-option label="需求变更 (demand)" value="demand" />
          </el-select>
        </el-col>
        <el-col :span="10" class="text-right">
          <span class="total-count-badge">共 {{ filteredReplies.length }} 条记录</span>
        </el-col>
      </el-row>
    </div>

    <!-- 新增 / 编辑表单区域 (点击新增或编辑时展开) -->
    <el-collapse-transition>
      <div v-if="isFormVisible" class="reply-form-card mb-4">
        <div class="form-card-title">
          <span>{{ editingId ? '编辑沟通记录 #' + editingId : '新增沟通记录' }}</span>
          <el-button
            circle
            size="small"
            :icon="Close"
            class="close-form-btn"
            @click="cancelForm"
          />
        </div>
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="90px"
          size="small"
          class="mt-2"
        >
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="沟通类型" prop="reply_type">
                <el-select v-model="formData.reply_type" style="width: 100%">
                  <el-option label="客户回复" value="customer" />
                  <el-option label="客户提问" value="question" />
                  <el-option label="我方答复" value="reply" />
                  <el-option label="需求变更" value="demand" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="提交人" prop="submitter_name">
                <el-input
                  v-model="formData.submitter_name"
                  placeholder="如: 张三 / 客户业务员"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="沟通日期" prop="reply_date">
                <el-date-picker
                  v-model="formData.reply_date"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="选择日期"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="详细内容" prop="reply_content">
            <el-input
              v-model="formData.reply_content"
              type="textarea"
              :rows="3"
              placeholder="请输入与客户往来的具体需求、疑问或答复说明..."
            />
          </el-form-item>
          <div class="form-card-footer text-right">
            <el-button size="small" @click="cancelForm">取消</el-button>
            <el-button
              type="primary"
              size="small"
              :loading="submitting"
              @click="submitForm"
            >
              保存记录
            </el-button>
          </div>
        </el-form>
      </div>
    </el-collapse-transition>

    <!-- 往来需求流式时间轴记录列表 -->
    <div v-loading="loading" class="reply-stream-container">
      <el-empty
        v-if="filteredReplies.length === 0 && !loading"
        description="暂无符合条件的客户往来沟通记录"
      />

      <el-timeline v-else class="reply-timeline">
        <el-timeline-item
          v-for="item in filteredReplies"
          :key="item.id"
          :timestamp="item.reply_date"
          placement="top"
          :type="getTimelineType(item.reply_type)"
        >
          <div class="reply-card shadow-sm">
            <div class="card-header">
              <div class="header-left">
                <span class="seq-label">{{ item.sequence_label || ('#' + item.id) }}</span>
                <el-tag
                  :type="getTagType(item.reply_type)"
                  size="small"
                  effect="dark"
                  class="type-badge me-2"
                >
                  {{ getTypeLabel(item.reply_type) }}
                </el-tag>
                <span class="submitter-name">
                  <el-icon class="me-1"><User /></el-icon>
                  {{ item.submitter_name || '未署名' }}
                </span>
              </div>
              <div class="header-actions">
                <el-button
                  type="primary"
                  link
                  size="small"
                  :icon="Edit"
                  @click="startEdit(item)"
                >
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定要删除这条往来记录吗？"
                  confirm-button-text="确定"
                  cancel-button-text="取消"
                  @confirm="handleDelete(item.id)"
                >
                  <template #reference>
                    <el-button
                      type="danger"
                      link
                      size="small"
                      :icon="Delete"
                    >
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
            <div class="card-body">
              <div class="reply-text">{{ item.reply_content }}</div>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <template #footer>
      <div class="dialog-footer text-right">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @fileoverview 客户往来需求与回复记录管理弹窗组件 (customer_reply_dialog.vue)
 * 提供关联单据/客户的往来需求列表展示、类型筛选、增删改查及 Excel 导出功能。
 */
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Download,
  Refresh,
  Search,
  Close,
  User,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import {
  customerReplyApi,
  CustomerReplyItem,
  CustomerReplyFormPayload,
} from '../../api/customerReply'

// Component Props & Emits
const props = defineProps<{
  modelValue?: boolean
  visible?: boolean
  piId?: number
  customerId?: number
  piNo?: string
  customerName?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  'update:visible': [val: boolean]
  'refresh': []
}>()

// 内部显隐控制状态（当父组件未通过 v-model / v-model:visible 绑定时作为兜底状态）
const internalVisible = ref(false)

// 对话框显隐状态双向联动
const dialogVisible = computed({
  get: () => {
    if (props.modelValue !== undefined) return props.modelValue
    if (props.visible !== undefined) return props.visible
    return internalVisible.value
  },
  set: (val: boolean) => {
    internalVisible.value = val
    emit('update:modelValue', val)
    emit('update:visible', val)
  },
})

// 响应式状态数据
const loading = ref(false)
const submitting = ref(false)
const exporting = ref(false)
const replies = ref<CustomerReplyItem[]>([])
const searchQuery = ref('')
const filterType = ref('')

// 表单控制
const isFormVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref()

const formData = ref<{
  reply_type: string
  submitter_name: string
  reply_date: string
  reply_content: string
}>({
  reply_type: 'customer',
  submitter_name: '客户代表',
  reply_date: new Date().toISOString().split('T')[0],
  reply_content: '',
})

const formRules = {
  reply_type: [{ required: true, message: '请选择沟通类型', trigger: 'change' }],
  reply_content: [{ required: true, message: '请输入沟通需求与详细内容', trigger: 'blur' }],
  reply_date: [{ required: true, message: '请选择沟通日期', trigger: 'change' }],
}

// 过滤后的回复列表
const filteredReplies = computed(() => {
  return replies.value.filter((item) => {
    // 基础类型匹配
    const matchType = !filterType.value || item.reply_type === filterType.value
    // 文本与提交人匹配
    const query = searchQuery.value.trim().toLowerCase()
    const matchQuery =
      !query ||
      item.reply_content.toLowerCase().includes(query) ||
      (item.submitter_name || '').toLowerCase().includes(query)
    return matchType && matchQuery
  })
})

/** 对话框打开时拉取数据 */
function handleOpen() {
  cancelForm()
  fetchReplies()
}

/** 拉取客户往来回复列表 */
async function fetchReplies() {
  loading.value = true
  try {
    if (props.piId) {
      const res = await customerReplyApi.getByPi(props.piId)
      replies.value = res.data || []
    } else if (props.customerId) {
      const res = await customerReplyApi.getByCustomer(props.customerId)
      replies.value = res.data || []
    } else {
      const res = await customerReplyApi.list({ limit: 100 })
      replies.value = res.data || []
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取客户往来需求记录失败')
  } finally {
    loading.value = false
  }
}

/** 显示新增表单 */
function showAddForm() {
  editingId.value = null
  formData.value = {
    reply_type: 'customer',
    submitter_name: '客户代表',
    reply_date: new Date().toISOString().split('T')[0],
    reply_content: '',
  }
  isFormVisible.value = true
}

/** 开启编辑状态 */
function startEdit(item: CustomerReplyItem) {
  editingId.value = item.id
  formData.value = {
    reply_type: item.reply_type || 'customer',
    submitter_name: item.submitter_name || '',
    reply_date: item.reply_date || new Date().toISOString().split('T')[0],
    reply_content: item.reply_content || '',
  }
  isFormVisible.value = true
}

/** 取消并隐藏表单 */
function cancelForm() {
  isFormVisible.value = false
  editingId.value = null
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

/** 提交表单保存记录 */
async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editingId.value) {
        // 更新记录
        await customerReplyApi.update(editingId.value, {
          reply_type: formData.value.reply_type,
          submitter_name: formData.value.submitter_name,
          reply_date: formData.value.reply_date,
          reply_content: formData.value.reply_content,
        })
        ElMessage.success('更新沟通需求记录成功')
      } else {
        // 新增记录
        const payload: CustomerReplyFormPayload = {
          pi_id: props.piId || 0,
          customer_id: props.customerId || 0,
          reply_type: formData.value.reply_type,
          submitter_name: formData.value.submitter_name,
          reply_date: formData.value.reply_date,
          reply_content: formData.value.reply_content,
        }
        await customerReplyApi.create(payload)
        ElMessage.success('新增沟通需求记录成功')
      }
      cancelForm()
      fetchReplies()
      emit('refresh')
    } catch (error: any) {
      ElMessage.error(error.message || '保存记录失败')
    } finally {
      submitting.value = false
    }
  })
}

/** 删除记录 */
async function handleDelete(id: number) {
  try {
    await customerReplyApi.remove(id)
    ElMessage.success('已成功删除该记录')
    fetchReplies()
    emit('refresh')
  } catch (error: any) {
    ElMessage.error(error.message || '删除记录失败')
  }
}

/** 导出 Excel 文件 */
async function handleExport() {
  if (!props.piId) {
    ElMessage.warning('当前未关联指定 PI 单号，无法导出')
    return
  }
  exporting.value = true
  try {
    const res = await customerReplyApi.exportExcel(props.piId, {
      customer_name: props.customerName || '',
    })
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `客户往来需求记录_${props.piNo || props.piId}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出 Excel 成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出 Excel 失败')
  } finally {
    exporting.value = false
  }
}

// 辅助样式标签映射函数
function getTagType(type?: string) {
  switch (type) {
    case 'question':
      return 'warning'
    case 'reply':
      return 'primary'
    case 'demand':
      return 'danger'
    case 'customer':
    default:
      return 'success'
  }
}

function getTypeLabel(type?: string) {
  switch (type) {
    case 'question':
      return '客户提问'
    case 'reply':
      return '我方答复'
    case 'demand':
      return '需求变更'
    case 'customer':
    default:
      return '客户回复'
  }
}

function getTimelineType(type?: string) {
  switch (type) {
    case 'question':
      return 'warning'
    case 'reply':
      return 'primary'
    case 'demand':
      return 'danger'
    case 'customer':
    default:
      return 'success'
  }
}

/** 打开对话框公开方法 */
function open() {
  dialogVisible.value = true
}

/** 关闭对话框公开方法 */
function close() {
  dialogVisible.value = false
}

defineExpose({
  open,
  close,
  fetchReplies,
})
</script>

<style scoped>
.customer-reply-dialog :deep(.el-dialog__body) {
  padding: 16px 24px;
}

.dialog-header-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 16px;
}

.info-tag {
  font-weight: 500;
  font-size: 13px;
}

.filter-toolbar {
  background: #ffffff;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
}

.total-count-badge {
  font-size: 12px;
  color: #64748b;
}

.reply-form-card {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 14px 16px;
  position: relative;
}

.form-card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  border-bottom: 1px solid #e0f2fe;
  padding-bottom: 8px;
}

.reply-stream-container {
  min-height: 220px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 8px;
}

.reply-timeline {
  padding-left: 4px;
  margin-top: 8px;
}

.reply-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 14px;
  transition: all 0.2s ease;
}

.reply-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px dashed #f1f5f9;
  padding-bottom: 6px;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.seq-label {
  font-weight: bold;
  color: #3b82f6;
  font-size: 13px;
}

.submitter-name {
  font-size: 12px;
  color: #64748b;
  display: inline-flex;
  align-items: center;
}

.card-body {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.6;
}

.reply-text {
  white-space: pre-wrap;
  word-break: break-all;
}

.me-1 { margin-right: 4px; }
.me-2 { margin-right: 8px; }
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.mt-2 { margin-top: 8px; }
.text-right { text-align: right; }
</style>
