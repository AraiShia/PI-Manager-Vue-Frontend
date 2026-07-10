<template>
  <div class="shipment-list-panel">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select
          v-model="localStatus"
          placeholder="全部状态"
          style="width: 130px"
          clearable
          @change="onStatusChange"
        >
          <el-option label="全部" :value="undefined" />
          <el-option label="待出货" :value="SHIPMENT_STATUS.PENDING" />
          <el-option label="出货中" :value="SHIPMENT_STATUS.IN_PROGRESS" />
          <el-option label="已出货" :value="SHIPMENT_STATUS.SHIPPED" />
          <el-option label="已到达" :value="SHIPMENT_STATUS.ARRIVED" />
        </el-select>

        <el-input
          v-model="localKeyword"
          placeholder="搜索出货单号/CI号/PI号..."
          clearable
          style="width: 250px"
          @clear="onSearch"
          @keyup.enter="onSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-button :icon="Refresh" @click="onRefresh">刷新</el-button>
      </div>
    </div>

    <!-- 表格（复刻 PyQt 11 列） -->
    <div class="table-wrapper">
      <el-table
        v-loading="store.loading"
        :data="store.list"
        stripe
        border
        height="100%"
        highlight-current-row
        @row-dblclick="onRowDoubleClick"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />

        <el-table-column prop="shipment_no" label="出货单号" min-width="160" show-overflow-tooltip />

        <el-table-column prop="ci_no" label="CI号" min-width="140" show-overflow-tooltip />

        <el-table-column prop="customs_no" label="报关单" min-width="140" show-overflow-tooltip />

        <el-table-column prop="pi_nos" label="PI号" min-width="160" show-overflow-tooltip />

        <el-table-column prop="total_amount" label="总金额" width="120" align="right">
          <template #default="{ row }">{{ row.total_amount?.toFixed(2) ?? '-' }}</template>
        </el-table-column>

        <el-table-column prop="total_cartons" label="总箱数" width="90" align="right">
          <template #default="{ row }">{{ row.total_cartons ?? '-' }}</template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <span
              class="status-badge"
              :style="{ backgroundColor: SHIPMENT_STATUS_COLOR[row.status] + '22', color: SHIPMENT_STATUS_COLOR[row.status] }"
            >
              {{ SHIPMENT_STATUS_TEXT[row.status] }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建日期" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="onViewDetail(row)">
              查看
            </el-button>
            <el-button size="small" type="success" link @click="onConfirm(row)">
              确认
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="store.page"
        v-model:page-size="store.pageSize"
        :total="store.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useShipmentStore } from '@/stores/shipmentStore'
import { shipmentsApi } from '@/api/shipments'
import {
  SHIPMENT_STATUS,
  SHIPMENT_STATUS_TEXT,
  SHIPMENT_STATUS_COLOR,
} from '@/types/shipment'
import type { Shipment } from '@/types/shipment'

const store = useShipmentStore()
const router = useRouter()

const localStatus = ref<number | undefined>(undefined)
const localKeyword = ref('')

onMounted(() => {
  store.fetchList()
})

function onStatusChange() {
  store.fetchList({ status: localStatus.value, keyword: localKeyword.value })
}

function onSearch() {
  store.fetchList({ status: localStatus.value, keyword: localKeyword.value })
}

function onRefresh() {
  store.fetchList({ status: localStatus.value, keyword: localKeyword.value })
}

function onPageChange(page: number) {
  store.fetchList({ page, status: localStatus.value, keyword: localKeyword.value })
}

function onSizeChange(size: number) {
  store.fetchList({ page: 1, page_size: size, status: localStatus.value, keyword: localKeyword.value })
}

function onRowDoubleClick(row: Shipment) {
  // 下一轮：路由到 /shipments/:id 详情页
  router.push(`/shipments/${row.id}`)
}

function onViewDetail(row: Shipment) {
  router.push(`/shipments/${row.id}`)
}

async function onConfirm(row: Shipment) {
  try {
    await ElMessageBox.confirm(`确认出货单 ${row.shipment_no}？`, '确认出货', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await shipmentsApi.confirmShipment(row.id)
    ElMessage.success('确认成功')
    store.fetchList()
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('确认失败', e)
    }
  }
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  return dateStr.slice(0, 16)
}
</script>

<style scoped>
.shipment-list-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: #fff;
}
.toolbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  gap: 12px;
  border-bottom: 1px solid #e4e7ed;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.table-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 0 24px;
}
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 12px 24px;
  border-top: 1px solid #e4e7ed;
}
</style>
