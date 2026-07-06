<template>
  <div class="order-detail-panel" v-loading="store.detailLoading">
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="onBack">返回订单列表</el-button>
        <div class="order-title">
          <span class="order-no">{{ store.currentOrder?.pi_no || '-' }}</span>
          <span class="customer-name">{{ store.currentOrder?.customer_name || '-' }}</span>
        </div>
      </div>

      <div class="header-center">
        <el-tag :type="statusTagType" effect="light" size="large">
          {{ store.currentOrder?.status_label || '-' }}
        </el-tag>
        <div class="payment-progress">
          <span class="progress-label">付款进度</span>
          <el-progress
            :percentage="Math.round(store.currentOrder?.payment_progress || 0)"
            :status="progressStatus"
            :stroke-width="10"
            style="width: 160px"
          />
        </div>
      </div>

      <div class="header-right">
        <el-button :icon="Upload" @click="onImportProduct">导入产品</el-button>
        <el-button :icon="Download" @click="onExportExcel">导出Excel</el-button>
        <el-button type="primary" :icon="Wallet" @click="onAddPayment">添加付款</el-button>
        <el-button type="success" :icon="ShoppingCart" @click="onPurchaseAll">采购全部</el-button>
        <el-button type="warning" :icon="Plus" @click="onSupplement">补充商品</el-button>
        <el-button type="danger" :icon="Van" @click="onShipment">出货</el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="store.detailItems"
        border
        stripe
        height="100%"
        highlight-current-row
        size="small"
        @row-contextmenu="onRowContextMenu"
        @cell-dblclick="onCellDblClick"
      >
        <el-table-column type="index" label="#" width="50" align="center" fixed="left" />

        <el-table-column label="A组：基础信息">
          <el-table-column prop="order_date" label="订单日期" width="110" align="center">
            <template #default="{ row }">
              {{ formatDate(row.order_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="pi_no" label="PI号" width="140" show-overflow-tooltip />
          <el-table-column prop="product_code" label="客户产品编号" width="130" fixed="left" show-overflow-tooltip />
          <el-table-column prop="oe_number" label="OE号" width="120" fixed="left" show-overflow-tooltip />
          <el-table-column prop="remark" label="客户需求/产品备注" width="150" show-overflow-tooltip />
          <el-table-column prop="product_name" label="产品名称" width="180" show-overflow-tooltip />
          <el-table-column prop="image_url" label="图片" width="70" align="center">
            <template #default="{ row }">
              <el-image
                v-if="row.image_url"
                :src="row.image_url"
                :preview-src-list="[row.image_url]"
                fit="cover"
                style="width: 60px; height: 40px; border-radius: 2px; cursor: pointer"
              />
              <span v-else class="no-image">暂无</span>
            </template>
          </el-table-column>
          <el-table-column prop="customer_model" label="客户型号" width="130" show-overflow-tooltip />
          <el-table-column prop="product_feature" label="产品特性" width="130" show-overflow-tooltip />
        </el-table-column>

        <el-table-column label="B组：价格财务">
          <el-table-column prop="quantity" label="数量" width="80" align="right" />
          <el-table-column prop="unit_price" label="报价" width="100" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.unit_price) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_amount" label="合计金额" width="110" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.total_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="latest_customer_reply" label="最新客户回复" width="140" show-overflow-tooltip />
          <el-table-column prop="customer_prepayment" label="客户预付款" width="110" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.customer_prepayment) }}
            </template>
          </el-table-column>
          <el-table-column prop="remaining_payment" label="待收尾款" width="110" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.remaining_payment) }}
            </template>
          </el-table-column>
          <el-table-column prop="estimated_usd_price" label="预估美金报价" width="120" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.estimated_usd_price) }}
            </template>
          </el-table-column>
          <el-table-column prop="estimated_margin" label="预估毛利率" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'text-success': row.estimated_margin >= 20 }">
                {{ row.estimated_margin ? row.estimated_margin.toFixed(1) + '%' : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="purchase_price" label="采购价格" width="100" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.purchase_price) }}
            </template>
          </el-table-column>
          <el-table-column prop="shipping_fee" label="运费" width="90" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.shipping_fee) }}
            </template>
          </el-table-column>
          <el-table-column prop="misc_fee" label="杂费" width="90" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.misc_fee) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_cost" label="总金额(成本)" width="120" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.total_cost) }}
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="C组：供应商采购">
          <el-table-column prop="factory_name" label="工厂简称" width="130" show-overflow-tooltip />
          <el-table-column prop="shop_url" label="店铺链接" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link
                v-if="row.shop_url"
                type="primary"
                :href="row.shop_url"
                target="_blank"
                :underline="false"
              >
                访问
              </el-link>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="delivery_date" label="交货日期" width="110" align="center">
            <template #default="{ row }">
              {{ formatDate(row.delivery_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="storage_status" label="是否已收货" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.storage_status === '已收货'" type="success" size="small">已收货</el-tag>
              <el-tag v-else-if="row.storage_status === '部分入库'" type="warning" size="small">部分入库</el-tag>
              <el-tag v-else type="info" size="small">未收货</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="factory_deposit" label="工厂订金" width="100" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.factory_deposit) }}
            </template>
          </el-table-column>
          <el-table-column prop="factory_balance" label="工厂尾款" width="100" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.factory_balance) }}
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="D组：物流入库">
          <el-table-column prop="stock_in_action" label="入库操作" width="100" align="center" />
          <el-table-column prop="stock_in_quantity" label="入库数量" width="90" align="right" />
          <el-table-column prop="packaging" label="包装方式" width="110" show-overflow-tooltip />
        </el-table-column>

        <el-table-column label="E组：产品细节">
          <el-table-column prop="purchase_option_name" label="采购选项/名称" width="140" show-overflow-tooltip />
          <el-table-column prop="product_detail" label="产品细节" width="150" show-overflow-tooltip />
          <el-table-column prop="factory_code" label="工厂编号" width="120" show-overflow-tooltip />
          <el-table-column prop="carton_size" label="纸箱尺寸" width="120" show-overflow-tooltip />
          <el-table-column prop="pack_spec" label="打包规格" width="110" show-overflow-tooltip />
          <el-table-column prop="carton_count" label="箱数" width="80" align="right" />
          <el-table-column prop="estimated_volume" label="预估体积(m³)" width="110" align="right">
            <template #default="{ row }">
              {{ row.estimated_volume ? row.estimated_volume.toFixed(4) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="carton_gross_weight" label="整箱毛重(kg)" width="110" align="right">
            <template #default="{ row }">
              {{ row.carton_gross_weight ? row.carton_gross_weight.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="total_weight" label="总重量(kg)" width="110" align="right">
            <template #default="{ row }">
              {{ row.total_weight ? row.total_weight.toFixed(2) : '-' }}
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="F组：其他属性">
          <el-table-column prop="brand" label="品牌" width="100" show-overflow-tooltip />
          <el-table-column prop="invoice_status" label="开票情况" width="100" show-overflow-tooltip />
        </el-table-column>

        <template #empty>
          <el-empty description="暂无产品数据" />
        </template>
      </el-table>
    </div>

    <div class="detail-footer">
      <div class="footer-item">
        <span class="footer-label">产品总数：</span>
        <span class="footer-value">{{ store.detailItems.length }}</span>
      </div>
      <div class="footer-item">
        <span class="footer-label">总金额：</span>
        <span class="footer-value amount">{{ formatAmount(totalAmountSum) }}</span>
      </div>
      <div class="footer-item">
        <span class="footer-label">已入库数量：</span>
        <span class="footer-value">{{ totalStockInQuantity }}</span>
      </div>
    </div>

    <el-dialog
      v-model="importDialogVisible"
      title="导入产品 - 预览与确认"
      width="900px"
      :close-on-click-modal="false"
      @close="onImportDialogClose"
    >
      <div v-loading="importLoading" class="import-dialog-content">
        <div class="import-section">
          <div class="section-title">列映射配置</div>
          <div class="mapping-grid">
            <div
              v-for="field in importFields"
              :key="field.key"
              class="mapping-item"
            >
              <span class="mapping-label">{{ field.label }}</span>
              <el-select
                v-model="columnMapping[field.key]"
                placeholder="选择Excel列"
                size="small"
                style="width: 180px"
              >
                <el-option
                  v-for="col in excelHeaders"
                  :key="col"
                  :label="col"
                  :value="col"
                />
                <el-option label="-- 不导入 --" value="" />
              </el-select>
            </div>
          </div>
        </div>

        <div class="import-section">
          <div class="section-title">
            数据预览
            <span class="preview-count">(共 {{ importedRawData.length }} 行，显示前20行)</span>
          </div>
          <div class="preview-table-wrapper">
            <el-table :data="previewData" border size="small" max-height="300">
              <el-table-column type="index" label="#" width="50" align="center" />
              <el-table-column
                v-for="col in excelHeaders"
                :key="col"
                :label="col"
                :min-width="120"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  {{ row[col] }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importSubmitting"
          @click="onConfirmImport"
        >
          确认导入 ({{ importedRawData.length }} 条)
        </el-button>
      </template>
    </el-dialog>

    <input
      ref="fileInputRef"
      type="file"
      accept=".xlsx,.xls"
      style="display: none"
      @change="onFileInputChange"
    />

    <teleport to="body">
      <div
        v-show="contextMenuVisible"
        class="context-menu"
        :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
        @click.stop
      >
        <ul class="context-menu-list">
          <template v-for="item in contextMenuItems" :key="item.action">
            <li v-if="item.divider" class="context-menu-divider"></li>
            <li
              v-else
              class="context-menu-item"
              :class="{ danger: item.danger }"
              @click="handleContextMenuAction(item.action)"
            >
              <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </li>
          </template>
        </ul>
      </div>
    </teleport>

    <!-- 对话框组件 -->
    <PaymentDialog ref="paymentDialogRef" @success="onDetailSuccess" />
    <SupplementDialog ref="supplementDialogRef" @success="onDetailSuccess" />
    <ProductEditDialog ref="productEditDialogRef" @closed="onDetailSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiUrl } from '@/api/base'
import {
  ArrowLeft,
  Upload,
  Download,
  Wallet,
  ShoppingCart,
  Plus,
  Van,
  Refresh,
  Box,
  Delete,
  Edit,
  Switch,
  Link,
} from '@element-plus/icons-vue'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'
import { orderSummaryApi } from '@/api/orderSummary'
import { nativeBridge } from '@/api/nativeBridge'
import type { OrderDetailItem } from '@/types/orderSummary'
import PaymentDialog from '@/components/order/PaymentDialog.vue'
import SupplementDialog from '@/components/order/SupplementDialog.vue'
import ProductEditDialog from '@/components/order/ProductEditDialog.vue'
import { ORDER_STATUS } from '@/constants/orderStatus'
import { format } from 'date-fns'
import * as XLSX from 'xlsx'

const store = useOrderSummaryStore()

interface ContextMenuItem {
  label: string
  icon?: any
  action: string
  divider?: boolean
  danger?: boolean
}

const contextMenuItems: ContextMenuItem[] = [
  { label: '采购该产品', action: 'purchase', icon: ShoppingCart },
  { label: '重新采购', action: 'repurchase', icon: Refresh },
  { label: '入库该产品', action: 'stockIn', icon: Box },
  { label: '', action: 'divider1', divider: true },
  { label: '删除商品', action: 'delete', icon: Delete, danger: true },
  { label: '', action: 'divider2', divider: true },
  { label: '编辑产品', action: 'edit', icon: Edit },
  { label: '更换供应商', action: 'changeSupplier', icon: Switch },
  { label: '访问店铺网站', action: 'openShop', icon: Link },
]

const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const currentContextRow = ref<OrderDetailItem | null>(null)

const importDialogVisible = ref(false)
const importLoading = ref(false)
const importSubmitting = ref(false)
const importedRawData = ref<any[]>([])
const excelHeaders = ref<string[]>([])
const columnMapping = reactive<Record<string, string>>({})
const fileInputRef = ref<HTMLInputElement | null>(null)
const paymentDialogRef = ref<InstanceType<typeof PaymentDialog>>()
const supplementDialogRef = ref<InstanceType<typeof SupplementDialog>>()
const productEditDialogRef = ref<InstanceType<typeof ProductEditDialog>>()

const importFields = [
  { key: 'product_code', label: '客户产品编号', required: true },
  { key: 'oe_number', label: 'OE号', required: false },
  { key: 'product_name', label: '产品名称', required: false },
  { key: 'quantity', label: '数量', required: true },
  { key: 'unit_price', label: '报价', required: false },
  { key: 'remark', label: '客户需求/产品备注', required: false },
  { key: 'customer_model', label: '客户型号', required: false },
  { key: 'product_feature', label: '产品特性', required: false },
]

const previewData = computed(() => importedRawData.value.slice(0, 20))

const statusTagType = computed(() => {
  const status = store.currentOrder?.status
  if (status == null) return 'info'
  const map: Record<number, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
    [ORDER_STATUS.CANCELLED]: 'info',
    [ORDER_STATUS.PENDING]: 'warning',
    [ORDER_STATUS.PROCESSING]: 'primary',
    [ORDER_STATUS.COMPLETED]: 'success',
  }
  return map[status] || 'info'
})

const progressStatus = computed(() => {
  const progress = store.currentOrder?.payment_progress || 0
  if (progress >= 100) return 'success'
  if (progress >= 30) return ''
  if (progress > 0) return 'warning'
  return 'exception'
})

const totalAmountSum = computed(() => {
  return store.detailItems.reduce((sum, item) => sum + (item.total_amount || 0), 0)
})

const totalStockInQuantity = computed(() => {
  return store.detailItems.reduce((sum, item) => sum + (item.stock_in_quantity || 0), 0)
})

onMounted(() => {
  document.addEventListener('click', hideContextMenu)
  document.addEventListener('contextmenu', hideContextMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', hideContextMenu)
  document.removeEventListener('contextmenu', hideContextMenu)
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

function onBack() {
  store.setViewMode('list')
}

async function onImportProduct() {
  if (!store.currentOrder) {
    ElMessage.warning('当前没有订单信息')
    return
  }

  try {
    importLoading.value = true
    let excelData: any[] = []

    if (nativeBridge.isAvailable) {
      const filePath = await nativeBridge.selectFile('Excel 文件 (*.xlsx *.xls)')
      if (!filePath) {
        importLoading.value = false
        return
      }
      excelData = await nativeBridge.readExcel(filePath)
    } else {
      if (fileInputRef.value) {
        fileInputRef.value.click()
        importLoading.value = false
        return
      }
    }

    if (excelData.length > 0) {
      processImportedData(excelData)
    }
  } catch (e) {
    console.error('Import failed:', e)
    ElMessage.error('导入失败：' + (e as Error).message)
  } finally {
    if (nativeBridge.isAvailable) {
      importLoading.value = false
    }
  }
}

function onFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importLoading.value = true
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = e.target?.result
      const workbook = XLSX.read(data, { type: 'binary' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { defval: '' })
      processImportedData(jsonData as any[])
    } catch (err) {
      console.error('Parse Excel failed:', err)
      ElMessage.error('解析Excel文件失败')
    } finally {
      importLoading.value = false
      if (fileInputRef.value) {
        fileInputRef.value.value = ''
      }
    }
  }
  reader.onerror = () => {
    ElMessage.error('读取文件失败')
    importLoading.value = false
  }
  reader.readAsBinaryString(file)
}

function processImportedData(data: any[]) {
  if (data.length === 0) {
    ElMessage.warning('Excel文件中没有数据')
    return
  }

  importedRawData.value = data
  const headers = Object.keys(data[0])
  excelHeaders.value = headers

  autoMapColumns(headers)
  importDialogVisible.value = true
}

function autoMapColumns(headers: string[]) {
  const keywordMap: Record<string, string[]> = {
    product_code: ['客户产品编号', '产品编号', '产品编码', 'product_code', 'product code'],
    oe_number: ['OE号', 'OE编号', 'oe_number', 'oe number'],
    product_name: ['产品名称', '品名', 'product_name', 'product name'],
    quantity: ['数量', '订货数量', 'quantity', 'qty'],
    unit_price: ['报价', '单价', '价格', 'unit_price', 'unit price', 'price'],
    remark: ['客户需求', '产品备注', '备注', 'remark', 'note'],
    customer_model: ['客户型号', '型号', 'customer_model', 'model'],
    product_feature: ['产品特性', '特性', 'product_feature', 'feature'],
  }

  for (const field of importFields) {
    columnMapping[field.key] = ''
    const keywords = keywordMap[field.key] || []
    for (const keyword of keywords) {
      const matched = headers.find(
        (h) => h.toLowerCase().includes(keyword.toLowerCase())
      )
      if (matched) {
        columnMapping[field.key] = matched
        break
      }
    }
  }
}

async function onConfirmImport() {
  const requiredFields = importFields.filter((f) => f.required)
  for (const field of requiredFields) {
    if (!columnMapping[field.key]) {
      ElMessage.warning(`请为"${field.label}"选择对应的Excel列`)
      return
    }
  }

  const orderId = store.currentOrder?.id
  if (!orderId) {
    ElMessage.warning('当前没有订单信息')
    return
  }

  try {
    importSubmitting.value = true

    const mappedItems = importedRawData.value.map((row) => {
      const item: Record<string, any> = {}
      for (const field of importFields) {
        const colName = columnMapping[field.key]
        if (colName) {
          item[field.key] = row[colName]
        }
      }
      return item
    })

    const res = await orderSummaryApi.importItems(orderId, mappedItems)
    if (res.data.code === 200) {
      ElMessage.success(`导入成功，共导入 ${res.data.data.imported} 条数据`)
      importDialogVisible.value = false
      await store.fetchOrderDetail(orderId)
    } else {
      ElMessage.error(res.data.message || '导入失败')
    }
  } catch (e) {
    console.error('Import submit failed:', e)
    ElMessage.error('导入失败：' + (e as Error).message)
  } finally {
    importSubmitting.value = false
  }
}

function onImportDialogClose() {
  importedRawData.value = []
  excelHeaders.value = []
  Object.keys(columnMapping).forEach((key) => {
    delete columnMapping[key]
  })
}

async function onExportExcel() {
  if (!store.currentOrder || store.detailItems.length === 0) {
    ElMessage.warning('当前没有可导出的数据')
    return
  }

  try {
    const exportData = store.detailItems.map((item) => ({
      订单日期: item.order_date,
      PI号: item.pi_no,
      客户产品编号: item.product_code,
      OE号: item.oe_number,
      客户需求产品备注: item.remark,
      产品名称: item.product_name,
      客户型号: item.customer_model,
      产品特性: item.product_feature,
      数量: item.quantity,
      报价: item.unit_price,
      合计金额: item.total_amount,
      最新客户回复: item.latest_customer_reply,
      客户预付款: item.customer_prepayment,
      待收尾款: item.remaining_payment,
      预估美金报价: item.estimated_usd_price,
      预估毛利率: item.estimated_margin,
      采购价格: item.purchase_price,
      运费: item.shipping_fee,
      杂费: item.misc_fee,
      总金额成本: item.total_cost,
      工厂简称: item.factory_name,
      店铺链接: item.shop_url,
      交货日期: item.delivery_date,
      是否已收货: item.storage_status,
      工厂订金: item.factory_deposit,
      工厂尾款: item.factory_balance,
      入库数量: item.stock_in_quantity,
      包装方式: item.packaging,
      采购选项名称: item.purchase_option_name,
      产品细节: item.product_detail,
      工厂编号: item.factory_code,
      纸箱尺寸: item.carton_size,
      打包规格: item.pack_spec,
      箱数: item.carton_count,
      预估体积: item.estimated_volume,
      整箱毛重: item.carton_gross_weight,
      总重量: item.total_weight,
      品牌: item.brand,
      开票情况: item.invoice_status,
    }))

    if (nativeBridge.isAvailable) {
      const defaultName = `订单_${store.currentOrder.pi_no}.xlsx`
      const savePath = await nativeBridge.saveFile(defaultName)
      if (savePath) {
        const success = await nativeBridge.writeExcel(savePath, exportData)
        if (success) {
          ElMessage.success('导出成功')
        } else {
          ElMessage.error('导出失败')
        }
      }
    } else {
      const worksheet = XLSX.utils.json_to_sheet(exportData)
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, '订单明细')
      const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
      const blob = new Blob([excelBuffer], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `订单_${store.currentOrder.pi_no}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    }
  } catch (e) {
    console.error('Export failed:', e)
    ElMessage.error('导出失败：' + (e as Error).message)
  }
}

function onAddPayment() {
  if (store.currentOrder) {
    paymentDialogRef.value?.open(store.currentOrder)
  }
}

function onPurchaseAll() {
  ElMessage.info('采购全部功能开发中')
}

function onSupplement() {
  if (store.currentOrder) {
    supplementDialogRef.value?.open(store.currentOrder)
  }
}

function onShipment() {
  ElMessage.info('出货功能开发中')
}

function onDetailSuccess() {
  // 刷新详情
  if (store.currentOrder?.id) {
    store.fetchOrderDetail(store.currentOrder.id)
  }
}

function onRowContextMenu(row: OrderDetailItem, event: MouseEvent) {
  event.preventDefault()
  currentContextRow.value = row
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
}

function hideContextMenu() {
  contextMenuVisible.value = false
  currentContextRow.value = null
}

async function handleContextMenuAction(action: string) {
  hideContextMenu()
  if (!currentContextRow.value) return
  
  const item = currentContextRow.value
  
  switch (action) {
    case 'purchase':
      // 调用采购接口
      try {
        const res = await fetch(apiUrl(`/api/pi/items/${item.id}/purchase`), { method: 'POST' })
        if (res.ok) {
          ElMessage.success('采购请求已提交')
        } else {
          ElMessage.error('采购失败')
        }
      } catch {
        ElMessage.error('采购请求失败')
      }
      break
    case 'repurchase':
      ElMessage.info('重新采购功能开发中')
      break
    case 'stockIn':
      // 调用入库接口
      try {
        const res = await fetch(apiUrl(`/api/pi/items/${item.id}/inbound`), { method: 'POST' })
        if (res.ok) {
          ElMessage.success('入库成功')
          onDetailSuccess()
        } else {
          ElMessage.error('入库失败')
        }
      } catch {
        ElMessage.error('入库请求失败')
      }
      break
    case 'delete':
      await deleteItem(item)
      break
    case 'edit':
      productEditDialogRef.value?.open(item, store.currentOrder?.customer_name, store.currentOrder?.customer_country)
      break
    case 'changeSupplier':
      ElMessage.info('更换供应商功能开发中')
      break
    case 'openShop':
      if (item.shop_url) {
        window.open(item.shop_url, '_blank')
      } else {
        ElMessage.warning('无店铺链接')
      }
      break
  }
}

async function deleteItem(item: OrderDetailItem) {
  try {
    await ElMessageBox.confirm('确定要删除该产品吗？', '确认删除', { type: 'warning' })
    const res = await fetch(apiUrl(`/api/pi/items/${item.id}`), { method: 'DELETE' })
    if (res.ok) {
      ElMessage.success('删除成功')
      onDetailSuccess()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function onCellDblClick(row: OrderDetailItem) {
  productEditDialogRef.value?.open(row, store.currentOrder?.customer_name, store.currentOrder?.customer_country)
}
</script>

<style scoped>
.order-detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
  background: #fff;
  box-sizing: border-box;
  position: relative;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.order-no {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.customer-name {
  font-size: 13px;
  color: #6b7280;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 24px;
}

.payment-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.table-container {
  flex: 1;
  min-height: 200px;
  overflow: hidden;
}

.detail-footer {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #f8fafc;
  border-radius: 8px;
  margin-top: 12px;
  gap: 32px;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-label {
  font-size: 13px;
  color: #6b7280;
}

.footer-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.footer-value.amount {
  color: #2563eb;
}

.text-success {
  color: #059669;
}

.no-image {
  font-size: 12px;
  color: #9ca3af;
}

.context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  padding: 6px 0;
}

.context-menu-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.15s;
}

.context-menu-item:hover {
  background-color: #eff6ff;
  color: #2563eb;
}

.context-menu-item.danger:hover {
  background-color: #fef2f2;
  color: #dc2626;
}

.context-menu-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}

.import-dialog-content {
  padding: 0 10px;
}

.import-section {
  margin-bottom: 20px;
}

.import-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #2563eb;
}

.preview-count {
  font-size: 12px;
  font-weight: normal;
  color: #6b7280;
  margin-left: 8px;
}

.mapping-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mapping-label {
  font-size: 13px;
  color: #4b5563;
  min-width: 110px;
  text-align: right;
  flex-shrink: 0;
}

.preview-table-wrapper {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}
</style>
