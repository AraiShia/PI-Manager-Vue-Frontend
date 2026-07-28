<template>
  <div class="pl-sheet-wrapper">
    <div class="pl-sheet">
      <h1 class="company-title">{{ plData.company_name }}</h1>
      <div class="pl-meta">
        <div><strong>PACKING LIST NO.:</strong> {{ plData.pi_no }}</div>
        <div><strong>DATE:</strong> {{ plData.order_date }}</div>
      </div>
      <h2 class="pl-main-title">PACKING LIST</h2>
      <table class="pl-table">
        <thead>
          <tr>
            <th>ITEM CODE</th>
            <th>DESCRIPTION</th>
            <th>QTY (PCS)</th>
            <th>CTNS</th>
            <th>N.W. (KG)</th>
            <th>G.W. (KG)</th>
            <th>CBM</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in plData.items" :key="index">
            <td>{{ item.code }}</td>
            <td>{{ item.description || item.name }}</td>
            <td class="text-center">{{ item.qty }}</td>
            <td class="text-center">{{ item.ctns || item.qty }}</td>
            <td class="text-right">{{ formatMoney(item.nw || item.qty * 15) }}</td>
            <td class="text-right">{{ formatMoney(item.gw || item.qty * 17) }}</td>
            <td class="text-right">{{ formatMoney(item.cbm || 0.07 * item.qty) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2" class="font-bold text-right">TOTAL:</td>
            <td class="text-center font-bold">{{ totalQuantity }}</td>
            <td class="text-center font-bold">{{ totalCtns }}</td>
            <td class="text-right font-bold">{{ formatMoney(totalNW) }}</td>
            <td class="text-right font-bold">{{ formatMoney(totalGW) }}</td>
            <td class="text-right font-bold">{{ formatMoney(totalCBM) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview PL 装箱单高保真渲染与导出组件
 */

import { reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

const props = withDefaults(defineProps<{ isEditMode?: boolean }>(), { isEditMode: false })
const store = useOrderSummaryStore()

const plData = reactive({
  company_name: 'HANGZHOU WEINA TRADE CO., LTD.',
  pi_no: 'PL20260521',
  order_date: '2026-05-21',
  items: [
    {
      code: 'WM-8012',
      name: 'Gaming Chair Ergonomic Design',
      description: 'Gaming Chair Ergonomic Design',
      qty: 970,
      ctns: 970,
      nw: 14550.0,
      gw: 16490.0,
      cbm: 68.5,
    },
  ],
})

function applyExportData(data: any) {
  if (!data) return
  if (data.company_name) plData.company_name = data.company_name
  if (data.pi_no) plData.pi_no = data.pi_no
  if (data.order_date) plData.order_date = data.order_date
  if (Array.isArray(data.items) && data.items.length > 0) {
    plData.items = JSON.parse(JSON.stringify(data.items))
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
  return plData.items.reduce((sum, item) => sum + (item.qty || 0), 0)
})

const totalCtns = computed(() => {
  return plData.items.reduce((sum, item) => sum + (item.ctns || item.qty || 0), 0)
})

const totalNW = computed(() => {
  return plData.items.reduce((sum, item) => sum + (item.nw || (item.qty || 0) * 15), 0)
})

const totalGW = computed(() => {
  return plData.items.reduce((sum, item) => sum + (item.gw || (item.qty || 0) * 17), 0)
})

const totalCBM = computed(() => {
  return plData.items.reduce((sum, item) => sum + (item.cbm || (item.qty || 0) * 0.07), 0)
})

function formatMoney(val: number): string {
  return (val || 0).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
}

function handlePrint() {
  window.print()
}

function handleExportExcel() {
  try {
    const wsData = [
      [plData.company_name],
      ['PACKING LIST'],
      [`PACKING LIST NO.: ${plData.pi_no}`, `DATE: ${plData.order_date}`],
      [],
      ['ITEM CODE', 'DESCRIPTION', 'QTY (PCS)', 'CTNS', 'N.W. (KG)', 'G.W. (KG)', 'CBM'],
      ...plData.items.map((it) => [
        it.code,
        it.description || it.name,
        it.qty,
        it.ctns || it.qty,
        it.nw || it.qty * 15,
        it.gw || it.qty * 17,
        it.cbm || it.qty * 0.07,
      ]),
      ['TOTAL:', '', totalQuantity.value, totalCtns.value, totalNW.value, totalGW.value, totalCBM.value],
    ]
    const ws = XLSX.utils.aoa_to_sheet(wsData)

    // 列宽配置 (!cols)
    ws['!cols'] = [
      { wch: 18 }, // ITEM CODE
      { wch: 32 }, // DESCRIPTION
      { wch: 12 }, // QTY
      { wch: 12 }, // CTNS
      { wch: 14 }, // N.W.
      { wch: 14 }, // G.W.
      { wch: 12 }, // CBM
    ]

    // 行高配置 (!rows)
    const rowsConfig: Array<{ hpt: number }> = [
      { hpt: 30 }, // 公司名称
      { hpt: 26 }, // PACKING LIST
      { hpt: 20 }, // PACKING LIST NO / DATE
      { hpt: 12 }, // 空白行
      { hpt: 24 }, // 表头
    ]
    plData.items.forEach(() => {
      rowsConfig.push({ hpt: 35 }) // 商品明细行高
    })
    rowsConfig.push({ hpt: 26 }) // TOTAL 行
    ws['!rows'] = rowsConfig

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'PL')
    XLSX.writeFile(wb, `Packing_List_${plData.pi_no}.xlsx`)
    ElMessage.success('PL 装箱单导出成功！')
  } catch (err) {
    ElMessage.error('导出失败：' + (err as Error).message)
  }
}

defineExpose({ handleExportExcel, handlePrint })
</script>

<style scoped>
.pl-sheet-wrapper { display: flex; justify-content: center; padding: 20px; }
.pl-sheet { width: 210mm; min-height: 297mm; padding: 15mm; background: #ffffff; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); box-sizing: border-box; }
.company-title { text-align: center; font-size: 20px; font-weight: bold; }
.pl-meta { display: flex; justify-content: space-between; margin: 12px 0; font-size: 13px; }
.pl-main-title { text-align: center; font-size: 18px; margin-bottom: 16px; }
.pl-table { width: 100%; border-collapse: collapse; }
.pl-table th, .pl-table td { border: 1px solid #000; padding: 6px 8px; font-size: 12px; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.font-bold { font-weight: bold; }
</style>
