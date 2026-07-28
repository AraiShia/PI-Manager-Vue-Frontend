<template>
  <div class="ci-sheet-wrapper">
    <div class="ci-sheet">
      <!-- 公司英文大标题 -->
      <h1 class="company-title">{{ ciData.company_name }}</h1>
      
      <div class="ci-meta">
        <div><strong>INVOICE NO.:</strong> {{ ciData.pi_no }}</div>
        <div><strong>DATE:</strong> {{ ciData.order_date }}</div>
      </div>

      <h2 class="ci-main-title">COMMERCIAL INVOICE</h2>

      <table class="ci-table">
        <thead>
          <tr>
            <th>ITEM CODE</th>
            <th>DESCRIPTION</th>
            <th>QUANTITY</th>
            <th>UNIT PRICE (USD)</th>
            <th>AMOUNT (USD)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in ciData.items" :key="index">
            <td>{{ item.code }}</td>
            <td>{{ item.description || item.name }}</td>
            <td class="text-center">{{ item.qty }}</td>
            <td class="text-right">${{ formatMoney(item.unit_price) }}</td>
            <td class="text-right font-bold">${{ formatMoney(item.qty * item.unit_price) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2" class="font-bold text-right">TOTAL:</td>
            <td class="text-center font-bold">{{ totalQuantity }}</td>
            <td></td>
            <td class="text-right font-bold">${{ formatMoney(totalAmount) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview CI 商业发票高保真渲染与导出组件
 */

import { reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

const props = withDefaults(defineProps<{ isEditMode?: boolean }>(), { isEditMode: false })
const store = useOrderSummaryStore()

const ciData = reactive({
  company_name: 'HANGZHOU WEINA TRADE CO., LTD.',
  pi_no: 'CI20260521',
  order_date: '2026-05-21',
  items: [
    {
      code: 'WM-8012',
      name: 'Gaming Chair Ergonomic Design',
      description: 'Gaming Chair Ergonomic Design',
      qty: 970,
      unit_price: 22.85,
    },
  ],
})

function applyExportData(data: any) {
  if (!data) return
  if (data.company_name) ciData.company_name = data.company_name
  if (data.pi_no) ciData.pi_no = data.pi_no
  if (data.order_date) ciData.order_date = data.order_date
  if (Array.isArray(data.items) && data.items.length > 0) {
    ciData.items = JSON.parse(JSON.stringify(data.items))
  }
}

watch(
  () => store.exportDocData,
  (newVal) => {
    if (newVal) applyExportData(newVal)
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  const cached = store.loadExportDocData()
  if (cached) applyExportData(cached)
})

const totalQuantity = computed(() => {
  return ciData.items.reduce((sum, item) => sum + (item.qty || 0), 0)
})

const totalAmount = computed(() => {
  return ciData.items.reduce((sum, item) => sum + (item.qty || 0) * (item.unit_price || 0), 0)
})

function formatMoney(val: number): string {
  return (val || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function handlePrint() {
  window.print()
}

function handleExportExcel() {
  try {
    const wsData = [
      [ciData.company_name],
      ['COMMERCIAL INVOICE'],
      [`INVOICE NO.: ${ciData.pi_no}`, `DATE: ${ciData.order_date}`],
      [],
      ['ITEM CODE', 'DESCRIPTION', 'QUANTITY', 'UNIT PRICE (USD)', 'AMOUNT (USD)'],
      ...ciData.items.map((it) => [
        it.code,
        it.description || it.name,
        it.qty,
        it.unit_price,
        it.qty * it.unit_price,
      ]),
      ['TOTAL:', '', totalQuantity.value, '', totalAmount.value],
    ]
    const ws = XLSX.utils.aoa_to_sheet(wsData)

    // 列宽配置 (!cols)
    ws['!cols'] = [
      { wch: 18 }, // ITEM CODE
      { wch: 32 }, // DESCRIPTION
      { wch: 14 }, // QUANTITY
      { wch: 18 }, // UNIT PRICE (USD)
      { wch: 18 }, // AMOUNT (USD)
    ]

    // 行高配置 (!rows)
    const rowsConfig: Array<{ hpt: number }> = [
      { hpt: 30 }, // 公司名称
      { hpt: 26 }, // COMMERCIAL INVOICE
      { hpt: 20 }, // INVOICE NO / DATE
      { hpt: 12 }, // 空白行
      { hpt: 24 }, // 表头
    ]
    ciData.items.forEach(() => {
      rowsConfig.push({ hpt: 35 }) // 商品明细行高
    })
    rowsConfig.push({ hpt: 26 }) // TOTAL 行
    ws['!rows'] = rowsConfig

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'CI')
    XLSX.writeFile(wb, `Commercial_Invoice_${ciData.pi_no}.xlsx`)
    ElMessage.success('CI 商业发票导出成功！')
  } catch (err) {
    ElMessage.error('导出失败：' + (err as Error).message)
  }
}

defineExpose({ handleExportExcel, handlePrint })
</script>

<style scoped>
.ci-sheet-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
}
.ci-sheet {
  width: 210mm;
  min-height: 297mm;
  padding: 15mm;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}
.company-title {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
}
.ci-meta {
  display: flex;
  justify-content: space-between;
  margin: 12px 0;
  font-size: 13px;
}
.ci-main-title {
  text-align: center;
  font-size: 18px;
  margin-bottom: 16px;
}
.ci-table {
  width: 100%;
  border-collapse: collapse;
}
.ci-table th, .ci-table td {
  border: 1px solid #000;
  padding: 6px 8px;
  font-size: 12px;
}
.text-center { text-align: center; }
.text-right { text-align: right; }
.font-bold { font-weight: bold; }
</style>
