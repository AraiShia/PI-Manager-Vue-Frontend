<template>
  <div class="purchase-sheet-wrapper">
    <div class="purchase-sheet">
      <h1 class="company-title">采购订单 / 采购合同 (PURCHASE INVOICE)</h1>
      <div class="purchase-meta">
        <div><strong>采购单号：</strong> {{ purchaseData.pi_no }}</div>
        <div><strong>签订日期：</strong> {{ purchaseData.order_date }}</div>
      </div>
      <table class="purchase-info-table">
        <tr>
          <td class="label-col">供方（供应商）：</td>
          <td>{{ purchaseData.seller.contact || '安吉威纳家具有限公司' }}</td>
          <td class="label-col">需方（买方）：</td>
          <td>{{ purchaseData.buyer.name || '杭州威纳贸易有限公司' }}</td>
        </tr>
      </table>
      <table class="purchase-table">
        <thead>
          <tr>
            <th>序号</th>
            <th>工厂产品编号</th>
            <th>产品名称</th>
            <th>规格装箱</th>
            <th>采购数量</th>
            <th>含税单价 (RMB)</th>
            <th>采购总金额 (RMB)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in purchaseData.items" :key="index">
            <td class="text-center">{{ index + 1 }}</td>
            <td>{{ item.code }}</td>
            <td>{{ item.name }}</td>
            <td class="text-center">{{ item.pcs_ctn || '1件/箱' }}</td>
            <td class="text-center">{{ item.qty }}</td>
            <td class="text-right">¥{{ formatMoney(item.unit_price) }}</td>
            <td class="text-right font-bold">¥{{ formatMoney(item.qty * item.unit_price) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="4" class="font-bold text-right">合计 TOTAL:</td>
            <td class="text-center font-bold">{{ totalQuantity }}</td>
            <td></td>
            <td class="text-right font-bold">¥{{ formatMoney(totalAmount) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview Purchase Invoice 采购合同高保真渲染与导出组件
 */

import { reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

const props = withDefaults(defineProps<{ isEditMode?: boolean }>(), { isEditMode: false })
const store = useOrderSummaryStore()

const purchaseData = reactive({
  company_name: '杭州威纳贸易有限公司',
  pi_no: 'PO20260521-01',
  order_date: '2026-05-21',
  seller: {
    contact: '安吉威纳家具有限公司',
  },
  buyer: {
    name: '杭州威纳贸易有限公司',
  },
  items: [
    {
      code: 'FACTORY-WM-8012',
      name: '电竞椅高级黑色款',
      pcs_ctn: '1件/箱',
      qty: 970,
      unit_price: 135.0,
    },
  ],
})

function applyExportData(data: any) {
  if (!data) return
  if (data.company_name) purchaseData.company_name = data.company_name
  if (data.pi_no) purchaseData.pi_no = data.pi_no
  if (data.order_date) purchaseData.order_date = data.order_date
  if (data.seller) Object.assign(purchaseData.seller, data.seller)
  if (data.buyer) Object.assign(purchaseData.buyer, data.buyer)
  if (Array.isArray(data.items) && data.items.length > 0) {
    purchaseData.items = JSON.parse(JSON.stringify(data.items))
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
  return purchaseData.items.reduce((sum, item) => sum + (item.qty || 0), 0)
})

const totalAmount = computed(() => {
  return purchaseData.items.reduce((sum, item) => sum + (item.qty || 0) * (item.unit_price || 0), 0)
})

function formatMoney(val: number): string {
  return (val || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function handlePrint() {
  window.print()
}

function handleExportExcel() {
  try {
    const wsData = [
      ['采购订单 / 采购合同 (PURCHASE INVOICE)'],
      [`采购单号：${purchaseData.pi_no}`, `签订日期：${purchaseData.order_date}`],
      [`供方：${purchaseData.seller.contact}`, '', `需方：${purchaseData.buyer.name}`, ''],
      [],
      ['序号', '工厂产品编号', '产品名称', '规格装箱', '采购数量', '含税单价 (RMB)', '采购总金额 (RMB)'],
      ...purchaseData.items.map((it, idx) => [
        idx + 1,
        it.code,
        it.name,
        it.pcs_ctn || '1件/箱',
        it.qty,
        it.unit_price,
        it.qty * it.unit_price,
      ]),
      ['合计 TOTAL:', '', '', '', totalQuantity.value, '', totalAmount.value],
    ]
    const ws = XLSX.utils.aoa_to_sheet(wsData)

    // 列宽配置 (!cols)
    ws['!cols'] = [
      { wch: 8 },  // 序号
      { wch: 18 }, // 工厂产品编号
      { wch: 28 }, // 产品名称
      { wch: 14 }, // 规格装箱
      { wch: 12 }, // 采购数量
      { wch: 18 }, // 含税单价 (RMB)
      { wch: 20 }, // 采购总金额 (RMB)
    ]

    // 行高配置 (!rows)
    const rowsConfig: Array<{ hpt: number }> = [
      { hpt: 30 }, // 采购合同标题
      { hpt: 22 }, // 采购单号 / 签订日期
      { hpt: 22 }, // 供方 / 需方
      { hpt: 12 }, // 空白行
      { hpt: 24 }, // 表头
    ]
    purchaseData.items.forEach(() => {
      rowsConfig.push({ hpt: 35 }) // 商品明细行高
    })
    rowsConfig.push({ hpt: 26 }) // 合计 TOTAL 行
    ws['!rows'] = rowsConfig

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'PO')
    XLSX.writeFile(wb, `Purchase_Invoice_${purchaseData.pi_no}.xlsx`)
    ElMessage.success('采购合同导出成功！')
  } catch (err) {
    ElMessage.error('导出失败：' + (err as Error).message)
  }
}

defineExpose({ handleExportExcel, handlePrint })
</script>

<style scoped>
.purchase-sheet-wrapper { display: flex; justify-content: center; padding: 20px; }
.purchase-sheet { width: 210mm; min-height: 297mm; padding: 15mm; background: #ffffff; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); box-sizing: border-box; }
.company-title { text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 16px; }
.purchase-meta { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13px; }
.purchase-info-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
.purchase-info-table td { border: 1px solid #000; padding: 6px 8px; font-size: 12px; }
.label-col { font-weight: bold; width: 18%; background: #f9fafb; }
.purchase-table { width: 100%; border-collapse: collapse; }
.purchase-table th, .purchase-table td { border: 1px solid #000; padding: 6px 8px; font-size: 12px; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.font-bold { font-weight: bold; }
</style>
