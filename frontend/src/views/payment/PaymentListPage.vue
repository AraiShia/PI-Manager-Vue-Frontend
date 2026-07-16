<template>
  <div class="payment-list-page">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索收据号/PI号/客户名"
          clearable
          style="width: 240px"
          @clear="onSearch"
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
        <el-button type="primary" :icon="Plus" @click="onAddPayment">添加收款</el-button>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table
        v-loading="loading"
        :data="list"
        stripe
        border
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="latest_receipt_no" label="最新收据号" min-width="140">
          <template #default="{ row }">
            {{ row.latest_receipt_no || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="pi_no" label="PI号" min-width="140">
          <template #default="{ row }">
            {{ row.pi_no || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="customer_name" label="客户" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.customer_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="total_amount" label="订单金额" width="130" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>

        <el-table-column prop="paid_amount" label="已收金额" width="130" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.paid_amount) }}
          </template>
        </el-table-column>

        <el-table-column prop="unpaid_amount" label="未收金额" width="130" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.unpaid_amount) }}
          </template>
        </el-table-column>

        <el-table-column label="收款记录" min-width="240">
          <template #default="{ row }">
            <div class="payment-slots">
              <el-tag v-for="payment in getPaymentSlots(row)" :key="payment.payment_id" type="success" effect="light">
                {{ formatAmount(payment.actual_amount) }} / {{ payment.arrival_date || '-' }}
              </el-tag>
              <span v-if="getPaymentSlots(row).length === 0">-</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="水单状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.latest_water_image" type="success" effect="light">已上传</el-tag>
            <el-tag v-else type="info" effect="light">未上传</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="onViewDetail(row)">
              查看
            </el-button>
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

    <!-- 添加/编辑收款对话框 -->
    <PaymentRecordDialog ref="paymentRecordDialogRef" @success="onDialogSuccess" />
    <!-- 收款详情抽屉 -->
    <PaymentDetailDrawer ref="paymentDetailDrawerRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { apiUrl } from '@/api/base'
import { PAYMENTS } from '@/api/endpoints'
import { format } from 'date-fns'
import type { ArCustomerPayment } from '@/types/payment'
import PaymentRecordDialog from '@/components/payment/PaymentRecordDialog.vue'
import PaymentDetailDrawer from '@/components/payment/PaymentDetailDrawer.vue'

type PaymentSlot = {
  payment_id: number
  actual_amount: number
  arrival_date?: string
}

type PaymentListRow = ArCustomerPayment & {
  pi_id: number
  total_amount?: number
  paid_amount?: number
  unpaid_amount?: number
  latest_receipt_no?: string
  latest_water_image?: string
  payment1?: PaymentSlot | null
  payment2?: PaymentSlot | null
  payment3?: PaymentSlot | null
}

const loading = ref(false)
const list = ref<PaymentListRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const initialPiNo = ref('')
const dateRange = ref<string[] | null>(null)

const route = useRoute()

// 子组件 ref
const paymentRecordDialogRef = ref<InstanceType<typeof PaymentRecordDialog>>()
const paymentDetailDrawerRef = ref<InstanceType<typeof PaymentDetailDrawer>>()

onMounted(() => {
  // 从 URL query 读取初始筛选条件
  if (route.query.pi_no) {
    initialPiNo.value = String(route.query.pi_no)
    searchKeyword.value = initialPiNo.value
  }
  fetchList()
})

function formatDate(dateStr: string | undefined): string {
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

function getPaymentSlots(row: PaymentListRow): PaymentSlot[] {
  return [row.payment1, row.payment2, row.payment3].filter(Boolean) as PaymentSlot[]
}

async function fetchList() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', String(page.value))
    params.append('page_size', String(pageSize.value))
    if (searchKeyword.value) {
      if (initialPiNo.value && searchKeyword.value === initialPiNo.value) {
        params.append('pi_no', searchKeyword.value)
      } else {
        params.append('keyword', searchKeyword.value)
      }
    }
    if (dateRange.value?.length === 2) {
      params.append('date_from', dateRange.value[0])
      params.append('date_to', dateRange.value[1])
    }
    const res = await fetch(apiUrl(PAYMENTS.receivables + '?' + params.toString()))
    if (res.ok) {
      const data = await res.json()
      list.value = data.items || data.list || []
      total.value = data.total || 0
    } else {
      ElMessage.error('获取收款列表失败')
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

function onDateRangeChange(val: string[] | null) {
  page.value = 1
  fetchList()
}

function onRefresh() {
  fetchList()
}

function onAddPayment() {
  paymentRecordDialogRef.value?.open()
}

async function onViewDetail(row: PaymentListRow) {
  if (row.id) {
    paymentDetailDrawerRef.value?.open(row)
    return
  }

  const res = await fetch(apiUrl(PAYMENTS.receivablesByPi(row.pi_id)))
  if (!res.ok) {
    ElMessage.error('获取收款详情失败')
    return
  }
  const payments = await res.json()
  if (payments?.length) {
    paymentDetailDrawerRef.value?.open(payments[0])
  } else {
    ElMessage.info('暂无收款记录')
  }
}

function onDialogSuccess() {
  fetchList()
}

function onPageChange(currentPage: number) {
  page.value = currentPage
  fetchList()
}

function onSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
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
</style>
