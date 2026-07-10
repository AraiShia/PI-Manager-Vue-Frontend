<template>
  <div class="order-list-panel">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索订单号/客户名"
          clearable
          style="width: 240px"
          @clear="onSearch"
          @keyup.enter="onSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="statusFilter" placeholder="全部状态" style="width: 130px" @change="onStatusChange">
          <el-option label="全部" :value="undefined" />
          <el-option label="草稿" :value="ORDER_STATUS.PENDING" />
          <el-option label="进行中" :value="ORDER_STATUS.PROCESSING" />
          <el-option label="待入库" value="pending_inbound"/>
          <el-option label="待出货" value="pending_shipment"/>
          <el-option label="已装柜" value="shipped"/>
          <el-option label="订单完结" value="completed"/>
          <el-option label="已废弃" :value="ORDER_STATUS.CANCELLED" />
        </el-select>

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
        <el-button type="danger" :icon="Delete" :disabled="!store.hasSelection" @click="onBatchDelete">
          批量删除
        </el-button>
        <el-button type="primary" :icon="Plus" @click="onNewOrder">新增订单</el-button>
        <el-button type="success" @click="onPaymentManagement">收款管理</el-button>
        <el-button type="warning" @click="onShipmentCreate">创建出货单</el-button>
        <el-button @click="onShipmentManagement">出货管理</el-button>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table
        v-loading="store.loading"
        :data="store.orders"
        stripe
        border
        height="100%"
        highlight-current-row
        @row-click="onRowClick"
        @row-dblclick="onRowDoubleClick"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />

        <el-table-column prop="pi_no" label="ORDER NO." min-width="160" />

        <el-table-column prop="customer_name" label="客户" min-width="160" show-overflow-tooltip />

        <el-table-column prop="created_at" label="订单日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="item_count" label="产品数" width="80" align="center" />

        <el-table-column prop="total_amount" label="总金额" width="130" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>

        <el-table-column prop="order_stage_label" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.order_stage_tag_type || 'primary'" effect="light">
              {{ row.order_stage_label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="paid_amount" label="已付款" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.paid_amount) }}
          </template>
        </el-table-column>

        <el-table-column prop="unpaid_amount" label="未付款" width="120" align="right">
          <template #default="{ row }">
            <span :class="{ 'text-success': row.unpaid_amount === 0 && row.paid_amount > 0 }">
              {{ formatAmount(row.unpaid_amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="payment_progress" label="付款进度" width="160">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round(row.payment_progress)"
              :status="progressStatus(row.payment_progress)"
              :stroke-width="10"
            />
          </template>
        </el-table-column>

        <el-table-column prop="stock_remaining" label="库存剩余" width="100" align="right">
          <template #default="{ row }">
            {{ row.stock_remaining }}
          </template>
        </el-table-column>

        <el-table-column label="添加付款" width="100" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="onAddPayment(row)">
              添加付款
            </el-button>
          </template>
        </el-table-column>

        <el-table-column label="PI操作" width="140" align="center">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click.stop="onPIOperation(row)">
              PI操作
            </el-button>
          </template>
        </el-table-column>

        <el-table-column label="管理" width="120" align="center">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(cmd: string) => onManageCommand(cmd, row)">
              <el-button size="small" type="primary" link>
                管理 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑订单</el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.status !== 0"
                    command="cancel"
                    divided
                    style="color: #e6a23c"
                  >废弃订单</el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.status !== 0"
                    command="delete"
                    style="color: #f56c6c"
                  >删除订单</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无订单数据" />
        </template>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="store.page"
        v-model:page-size="store.pageSize"
        :total="store.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="onSizeChange"
        @current-change="onPageChange"
      />
    </div>

    <!-- 对话框组件 -->
    <NewOrderDialog ref="newOrderDialogRef" @success="onNewOrderSuccess" />
    <PaymentDialog ref="paymentDialogRef" @success="onPaymentSuccess" />
    <PiOperationDialog ref="piDialogRef" @success="onPiSuccess" />
    <ShipmentCreateDialog ref="shipmentCreateDialogRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Delete, ArrowDown } from '@element-plus/icons-vue'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'
import { orderSummaryApi } from '@/api/orderSummary'
import ShipmentCreateDialog from '@/components/shipment/ShipmentCreateDialog.vue'
import type { OrderListItem, OrderListFilter } from '@/types/orderSummary'
import { ORDER_STATUS } from '@/constants/orderStatus'
import { format } from 'date-fns'
import { apiUrl } from '@/api/base'
import NewOrderDialog from '@/components/order/NewOrderDialog.vue'
import PaymentDialog from '@/components/order/PaymentDialog.vue'
import PiOperationDialog from '@/components/order/PiOperationDialog.vue'

const store = useOrderSummaryStore()
const router = useRouter()
const shipmentCreateDialogRef = ref()

const searchKeyword = ref('')
const statusFilter = ref<number | string | undefined>(undefined)
const dateRange = ref<string[] | null>(null)
const currentRow = ref<OrderListItem | null>(null)

// 对话框 ref
const newOrderDialogRef = ref<InstanceType<typeof NewOrderDialog>>()
const paymentDialogRef = ref<InstanceType<typeof PaymentDialog>>()
const piDialogRef = ref<InstanceType<typeof PiOperationDialog>>()

onMounted(() => {
  store.fetchOrders()
})

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd')
  } catch {
    return dateStr
  }
}

function formatAmount(amount: number | undefined | null): string {
  if (amount == null || isNaN(amount)) return '-'
  return amount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function statusTagType(status: number): 'success' | 'warning' | 'info' | 'primary' {
  const map: Record<number, 'success' | 'warning' | 'info' | 'primary'> = {
    [ORDER_STATUS.CANCELLED]: 'info',
    [ORDER_STATUS.PENDING]: 'warning',
    [ORDER_STATUS.PROCESSING]: 'primary',
    [ORDER_STATUS.COMPLETED]: 'success',
  }
  return map[status] || 'info'
}

function progressStatus(progress: number): '' | 'success' | 'warning' | 'exception' {
  if (progress >= 100) return 'success'
  if (progress >= 30) return ''
  if (progress > 0) return 'warning'
  return 'exception'
}

function applyFilter(filterUpdate: Partial<OrderListFilter>) {
  store.setFilter(filterUpdate)
  store.fetchOrders({ page: 1 })
}

function onRowClick(row: OrderListItem) {
  currentRow.value = row
}

function onRowDoubleClick(row: OrderListItem) {
  store.fetchOrderDetail(row.id)
}

function onSelectionChange(selection: OrderListItem[]) {
  const ids = new Set(selection.map((item) => item.id))
  store.selectedOrderIds = ids
}

function onSearch() {
  applyFilter({ search: searchKeyword.value || undefined })
}

function onStatusChange() {
  const val = statusFilter.value
  if (typeof val === 'number') {
    applyFilter({ status: val, order_stage: undefined })
  } else {
    applyFilter({ status: undefined, order_stage: val })
  }
}

function onDateRangeChange(val: string[] | null) {
  if (val && val.length === 2) {
    applyFilter({ date_from: val[0], date_to: val[1] })
  } else {
    applyFilter({ date_from: undefined, date_to: undefined })
  }
}

function onRefresh() {
  store.fetchOrders()
}

// 新增订单
function onNewOrder() {
  newOrderDialogRef.value?.open()
}

function onNewOrderSuccess() {
  store.fetchOrders()
}

// 批量删除
async function onBatchDelete() {
  if (store.selectedOrderIds.size === 0) {
    ElMessage.warning('请先选择要删除的订单')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${store.selectedOrderIds.size} 个订单吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    
    const deletePromises = Array.from(store.selectedOrderIds).map(id =>
      fetch(apiUrl(`/api/pi/${id}`), { method: 'DELETE' })
    )
    
    const results = await Promise.all(deletePromises)
    const successCount = results.filter(r => r.ok).length
    
    ElMessage.success(`成功删除 ${successCount} 个订单`)
    store.clearSelection()
    store.fetchOrders()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 添加付款
function onAddPayment(row: OrderListItem) {
  paymentDialogRef.value?.open(row)
}

function onPaymentSuccess() {
  store.fetchOrders()
}

// PI操作
function onPIOperation(row: OrderListItem) {
  piDialogRef.value?.open(row)
}

function onPiSuccess() {
  store.fetchOrders()
}

// 订单管理下拉操作
async function onManageCommand(cmd: string, row: OrderListItem) {
  if (cmd === 'edit') {
    onEdit(row)
  } else if (cmd === 'cancel') {
    try {
      await ElMessageBox.confirm(
        `确定废弃订单「${row.pi_no}」？废弃后订单将无法进行采购/入库操作。`,
        '废弃订单',
        { type: 'warning', confirmButtonText: '废弃', cancelButtonText: '取消' }
      )
      await orderSummaryApi.updatePiStatus(row.id, { status: 0 })
      ElMessage.success('订单已废弃')
      store.fetchOrders()
    } catch {
      // 用户取消
    }
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定删除订单「${row.pi_no}」？此操作不可恢复！`,
        '删除订单',
        { type: 'error', confirmButtonText: '删除', cancelButtonText: '取消' }
      )
      await orderSummaryApi.deletePi(row.id)
      ElMessage.success('订单已删除')
      store.fetchOrders()
    } catch {
      // 用户取消
    }
  }
}

// 编辑
function onEdit(row: OrderListItem) {
  ElMessage.info('订单编辑功能开发中')
}

// 收款管理
function onPaymentManagement() {
  if (currentRow.value) {
    router.push({
      path: '/payments',
      query: {
        pi_no: currentRow.value.pi_no,
        customer_name: currentRow.value.customer_name,
      },
    })
  } else {
    router.push('/payments')
  }
}

function onShipmentCreate() {
  shipmentCreateDialogRef.value?.open()
}

function onShipmentManagement() {
  router.push('/shipments')
}

function onPageChange(page: number) {
  store.fetchOrders({ page })
}

function onSizeChange(size: number) {
  store.fetchOrders({ page: 1, page_size: size })
}
</script>

<style scoped>
.order-list-panel {
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
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-left,
.toolbar-right {
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

.text-success {
  color: #67c23a;
}
</style>
