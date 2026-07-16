<template>
  <div class="purchase-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索采购单号 / PI号 / 供应商"
          clearable
          style="width: 240px"
          @keyup.enter="loadData"
        />
        <el-select v-model="status" placeholder="状态" clearable style="width: 120px; margin-left: 8px">
          <el-option label="草稿" :value="1" />
          <el-option label="已确认" :value="2" />
          <el-option label="已入库" :value="3" />
        </el-select>
        <el-button type="primary" style="margin-left: 8px" :loading="loading" @click="loadData">搜索</el-button>
      </div>
      <div class="toolbar-right">
        <el-button :loading="loading" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <el-table :data="list" v-loading="loading" stripe class="purchase-table">
      <el-table-column prop="po_no" label="采购单号" min-width="140" />
      <el-table-column prop="pi_no" label="PI号" min-width="120" />
      <el-table-column prop="supplier_name" label="供应商" min-width="140" />
      <el-table-column label="金额" min-width="100">
        <template #default="{ row }">
          {{ row.total_amount }} {{ row.currency }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 1"
            type="success"
            size="small"
            link
            :loading="row._confirming"
            @click="onConfirm(row)"
          >确认</el-button>
          <el-button
            v-if="row.status === 2"
            type="warning"
            size="small"
            link
            :loading="row._inbounding"
            @click="onInbound(row)"
          >入库</el-button>
          <el-button
            type="info"
            size="small"
            link
            @click="onViewInvoice(row)"
          >发票</el-button>
          <el-button
            type="primary"
            size="small"
            link
            :loading="row._exporting"
            @click="onExportContract(row)"
          >合同</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  normalizePurchaseListPayload,
  purchaseApi,
  type PurchaseOrderSummary,
} from '@/api/purchase'

const loading = ref(false)
const list = ref<PurchaseOrderSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const status = ref<number | undefined>(undefined)

function statusLabel(s: number) {
  return { 1: '草稿', 2: '已确认', 3: '已入库' }[s] ?? '未知'
}

function statusType(s: number) {
  return { 1: 'info', 2: 'warning', 3: 'success' }[s] as any
}

async function loadData() {
  loading.value = true
  try {
    const res = await purchaseApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: status.value,
    })
    const result = normalizePurchaseListPayload(res.data)
    list.value = result.data.map((item: PurchaseOrderSummary) => ({
      ...item,
      _confirming: false,
      _inbounding: false,
      _exporting: false,
    }))
    total.value = result.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function onConfirm(row: any) {
  row._confirming = true
  try {
    await purchaseApi.confirm(row.id)
    ElMessage.success('确认成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '确认失败')
  } finally {
    row._confirming = false
  }
}

async function onInbound(row: any) {
  row._inbounding = true
  try {
    await purchaseApi.inbound(row.id)
    ElMessage.success('入库成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '入库失败')
  } finally {
    row._inbounding = false
  }
}

async function onViewInvoice(row: any) {
  try {
    const res = await purchaseApi.getInvoiceUrl(row.id)
    const url = res.data?.data?.url
    if (url) {
      window.open(url, '_blank')
    } else {
      ElMessage.info('暂无发票')
    }
  } catch (e: any) {
    ElMessage.info('暂无发票')
  }
}

async function onExportContract(row: any) {
  row._exporting = true
  try {
    const res = await purchaseApi.exportContract(row.id)
    const blob = res.data as unknown as Blob
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = `Contract_${row.po_no}.xlsx`
    a.click()
    URL.revokeObjectURL(objectUrl)
    ElMessage.success('合同已导出')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '导出失败')
  } finally {
    row._exporting = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.purchase-page {
  padding: 16px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
}
.purchase-table {
  width: 100%;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
