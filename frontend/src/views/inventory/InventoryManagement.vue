<template>
  <div class="inventory-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">库存管理</h2>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="onAddInventory">
          新建库存
        </el-button>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-select v-model="filters.stockType" clearable placeholder="全部状态" style="width: 140px" @change="loadData">
        <el-option label="采购在途" :value="1" />
        <el-option label="待入库" :value="2" />
        <el-option label="已入库" :value="3" />
        <el-option label="历史库存" :value="4" />
      </el-select>

      <el-input
        v-model="filters.search"
        placeholder="搜索 OE号 / 产品编号 / 客户名"
        clearable
        style="width: 260px"
        :prefix-icon="Search as any"
        @clear="loadData"
        @keyup.enter="loadData"
      />
    </div>

    <!-- 统计概览 -->
    <div v-if="dashboard" class="stats-row">
      <div class="stat-card">
        <div class="stat-label">总记录</div>
        <div class="stat-value">{{ dashboard.total_records }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总库存</div>
        <div class="stat-value">{{ formatQty(dashboard.total_quantity) }}</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">采购在途</div>
        <div class="stat-value">{{ formatQty(dashboard.in_transit_quantity) }}</div>
      </div>
      <div class="stat-card blue">
        <div class="stat-label">待入库</div>
        <div class="stat-value">{{ formatQty(dashboard.pending_inbound_quantity) }}</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">已入库</div>
        <div class="stat-value">{{ formatQty(dashboard.stocked_quantity) }}</div>
      </div>
    </div>

    <!-- 主列表 -->
    <div class="table-wrapper">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        @row-click="onRowClick"
        @row-dblclick="onRowDblClick"
      >
        <el-table-column type="index" width="50" label="#" />
        <el-table-column label="OE号" prop="oe_number" min-width="160" show-overflow-tooltip />
        <el-table-column label="产品编号" prop="product_code" min-width="130" show-overflow-tooltip />
        <el-table-column label="客户" prop="customer_name" min-width="120" show-overflow-tooltip />
        <el-table-column label="供应商" prop="supplier_name" min-width="120" show-overflow-tooltip />
        <el-table-column label="总数量" prop="total_quantity" width="90" align="right">
          <template #default="{ row }">
            <span :class="row.total_quantity === 0 ? 'text-red' : ''">
              {{ formatQty(row.total_quantity) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="在途" prop="shipped_quantity" width="80" align="right">
          <template #default="{ row }">
            {{ formatQty(row.shipped_quantity) }}
          </template>
        </el-table-column>
        <el-table-column label="待入库" prop="pending_quantity" width="90" align="right">
          <template #default="{ row }">
            {{ formatQty(row.pending_quantity) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.stock_type)" size="small">
              {{ statusLabel(row.stock_status_color || row.stock_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="库位" prop="current_location" width="110" show-overflow-tooltip />
        <el-table-column label="采购价" prop="purchase_price" width="100" align="right">
          <template #default="{ row }">
            {{ row.purchase_price != null ? `$${Number(row.purchase_price).toFixed(2)}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="备注" prop="remark" min-width="140" show-overflow-tooltip />
        <el-table-column label="入库时间" prop="created_at" width="150">
          <template #default="{ row }">
            {{ row.created_at ? formatDate(row.created_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="onTransition(row)">
              状态
            </el-button>
            <el-button link type="primary" size="small" @click.stop="onEdit(row)">
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click.stop="onDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- 状态流转弹窗 -->
    <el-dialog v-model="transitionDialogVisible" title="库存状态流转" width="420px">
      <el-form label-width="80px">
        <el-form-item label="当前状态">
          <el-tag :type="statusTagType(currentItem?.stock_type)">
            {{ statusLabel(currentItem?.stock_status_color || currentItem?.stock_type) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="目标状态" required>
          <el-select v-model="transitionTarget" style="width: 100%">
            <el-option
              v-for="opt in availableTransitions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="transitionRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transitionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="transitionLoading" @click="confirmTransition">
          确认流转
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="isEditMode ? '编辑库存' : '新建库存'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="产品ID" prop="product_id">
          <el-input-number v-model="editForm.product_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="客户ID" prop="customer_id">
          <el-input-number v-model="editForm.customer_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="editForm.quantity" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="采购价">
          <el-input-number v-model="editForm.purchase_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="库位">
          <el-input v-model="editForm.current_location" placeholder="如：WAREHOUSE" />
        </el-form-item>
        <el-form-item label="供应商ID">
          <el-input-number v-model="editForm.supplier_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="confirmEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { inventoryApi } from '@/api/inventory'
import type { InventoryItem, InventoryTransitionPayload } from '@/types/inventory'

// ---------- 状态映射 ----------
const STATUS_LABEL: Record<string, string> = {
  yellow: '采购在途', blue: '待入库', green: '已入库', black: '历史库存',
}
const STATUS_TAG_MAP: Record<string, string> = {
  yellow: 'warning', blue: '', green: 'success', black: 'info',
}

function statusLabel(val: string | number | undefined): string {
  if (!val) return '-'
  if (typeof val === 'number') {
    const map: Record<number, string> = { 1: '采购在途', 2: '待入库', 3: '已入库', 4: '历史库存' }
    return map[val] ?? String(val)
  }
  return STATUS_LABEL[val] ?? val
}
function statusTagType(val: number | undefined): string {
  if (!val) return 'info'
  const map: Record<number, string> = { 1: 'warning', 2: '', 3: 'success', 4: 'info' }
  return map[val] ?? 'info'
}

// ---------- 允许的流转 ----------
const TRANSITIONS: Record<number, { value: number; label: string }[]> = {
  1: [{ value: 2, label: '待入库' }],
  2: [{ value: 3, label: '已入库' }],
  3: [{ value: 4, label: '历史库存' }],
}

function formatQty(v: number | undefined | null): string {
  if (v == null) return '0'
  return Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}
function formatDate(iso: string): string {
  if (!iso) return '-'
  return iso.slice(0, 16).replace('T', ' ')
}

// ---------- 数据 ----------
const loading = ref(false)
const tableData = ref<InventoryItem[]>([])
const dashboard = ref<{ total_records: number; total_quantity: number; in_transit_quantity: number; pending_inbound_quantity: number; stocked_quantity: number } | null>(null)

const filters = reactive({
  stockType: null as number | null,
  search: '',
})
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }
    if (filters.stockType) params.stock_type = filters.stockType

    const [invRes, dashRes] = await Promise.allSettled([
      inventoryApi.list(params as Parameters<typeof inventoryApi.list>[0]),
      inventoryApi.dashboard(),
    ])

    if (invRes.status === 'fulfilled') {
      tableData.value = invRes.value.data || []
      // 后端列表没有 total，可根据数据量估算
      if (tableData.value.length === pagination.pageSize) {
        pagination.total = (pagination.page) * pagination.pageSize + 1
      } else {
        pagination.total = (pagination.page - 1) * pagination.pageSize + tableData.value.length
      }
    }

    if (dashRes.status === 'fulfilled') {
      dashboard.value = dashRes.value.data
    }
  } catch (e) {
    console.error('[InventoryManagement] 加载失败', e)
    ElMessage.error('加载库存数据失败')
  } finally {
    loading.value = false
  }
}

// ---------- 状态流转 ----------
const transitionDialogVisible = ref(false)
const transitionLoading = ref(false)
const currentItem = ref<InventoryItem | null>(null)
const transitionTarget = ref<number | null>(null)
const transitionRemark = ref('')

const availableTransitions = computed(() => {
  if (!currentItem.value) return []
  return TRANSITIONS[currentItem.value.stock_type] || []
})

function onTransition(row: InventoryItem) {
  currentItem.value = row
  transitionTarget.value = null
  transitionRemark.value = ''
  transitionDialogVisible.value = true
}

async function confirmTransition() {
  if (!transitionTarget.value || !currentItem.value) {
    ElMessage.warning('请选择目标状态')
    return
  }
  transitionLoading.value = true
  try {
    await inventoryApi.transition(currentItem.value.id, {
      target_status: transitionTarget.value,
      remark: transitionRemark.value || undefined,
    })
    ElMessage.success('状态流转成功')
    transitionDialogVisible.value = false
    loadData()
  } catch {
    ElMessage.error('状态流转失败')
  } finally {
    transitionLoading.value = false
  }
}

// ---------- 新建 / 编辑 ----------
const editDialogVisible = ref(false)
const editLoading = ref(false)
const isEditMode = ref(false)
const editFormRef = ref<FormInstance>()
const currentEditId = ref<number | null>(null)
const editForm = reactive({
  product_id: null as number | null,
  customer_id: null as number | null,
  quantity: null as number | null,
  purchase_price: null as number | null,
  current_location: '',
  supplier_id: null as number | null,
  remark: '',
})
const editRules: FormRules = {
  product_id: [{ required: true, message: '请输入产品ID', trigger: 'blur' }],
  customer_id: [{ required: true, message: '请输入客户ID', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}

function onAddInventory() {
  isEditMode.value = false
  currentEditId.value = null
  Object.assign(editForm, {
    product_id: null, customer_id: null, quantity: null,
    purchase_price: null, current_location: 'WAREHOUSE', supplier_id: null, remark: '',
  })
  editDialogVisible.value = true
}

function onEdit(row: InventoryItem) {
  isEditMode.value = true
  currentEditId.value = row.id
  Object.assign(editForm, {
    product_id: row.product_id,
    customer_id: row.customer_id,
    quantity: row.total_quantity,
    purchase_price: row.purchase_price,
    current_location: row.current_location || '',
    supplier_id: row.supplier_id,
    remark: row.remark || '',
  })
  editDialogVisible.value = true
}

async function confirmEdit() {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    editLoading.value = true
    try {
      const payload: Record<string, unknown> = {
        product_id: editForm.product_id,
        customer_id: editForm.customer_id,
        quantity: editForm.quantity,
        purchase_price: editForm.purchase_price,
        current_location: editForm.current_location || undefined,
        supplier_id: editForm.supplier_id || undefined,
        remark: editForm.remark || undefined,
      }
      if (isEditMode.value && currentEditId.value) {
        await inventoryApi.update(currentEditId.value, payload)
      } else {
        await inventoryApi.create(payload)
      }
      ElMessage.success(isEditMode.value ? '更新成功' : '创建成功')
      editDialogVisible.value = false
      loadData()
    } catch {
      ElMessage.error(isEditMode.value ? '更新失败' : '创建失败')
    } finally {
      editLoading.value = false
    }
  })
}

// ---------- 删除 ----------
async function onDelete(row: InventoryItem) {
  await ElMessageBox.confirm(`确定删除该库存记录（${row.oe_number || row.product_code}）？`, '确认删除', { type: 'warning' })
  try {
    await inventoryApi.remove(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ---------- 行交互 ----------
function onRowClick() {}
function onRowDblClick() {}

onMounted(loadData)
</script>

<style scoped>
.inventory-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.toolbar {
  display: flex;
  gap: 12px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.stats-row {
  display: flex;
  gap: 12px;
  padding: 12px 24px;
  background: #fff;
}
.stat-card {
  flex: 1;
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  text-align: center;
}
.stat-card.yellow { background: #fefce8; border-color: #fde047; }
.stat-card.blue   { background: #eff6ff; border-color: #93c5fd; }
.stat-card.green  { background: #f0fdf4; border-color: #86efac; }
.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.table-wrapper {
  flex: 1;
  padding: 0 24px;
  overflow: auto;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 12px 24px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}
.text-red { color: #ef4444; }
</style>
