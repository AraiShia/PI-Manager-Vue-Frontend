<template>  <div class="order-detail-panel" v-loading="store.detailLoading">
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="onBack">返回订单列表</el-button>
        <div class="order-title">
          <span class="order-no">{{ store.currentOrder?.pi_no || '-' }}</span>
          <span class="order-date" v-if="store.currentOrder?.created_at">{{ formatDate(store.currentOrder?.created_at) }}</span>
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
        <el-popover
          placement="bottom-end"
          :width="300"
          trigger="click"
        >
          <template #reference>
            <el-button :icon="Setting" plain>设置列</el-button>
          </template>
          <template #default>
            <div class="col-filter-panel">
              <div class="col-filter-title">显示 / 隐藏列</div>
              <div class="col-filter-grid">
                <el-checkbox
                  v-for="col in columnVisibilityOptions"
                  :key="col.key"
                  v-model="colVisible[col.key]"
                  :label="col.locked ? `${col.label}（锁定）` : col.label"
                  :disabled="col.locked"
                />
              </div>
              <el-divider style="margin: 8px 0;" />
              <el-button
                size="small"
                type="primary"
                style="width: 100%;"
                @click="onRestoreImportOrder"
              >
                恢复导入顺序
              </el-button>
            </div>
          </template>
        </el-popover>
        <el-button :icon="Download" @click="onExportExcel">导出Excel</el-button>
        <el-tooltip :content="formalRecordTooltip" placement="bottom">
          <el-button
            v-if="!hasFormalRecord"
            type="warning"
            plain
            :loading="formalRecordLoading || formalRecordSaving"
            @click="onSaveFormalRecord"
          >
            保存正式纪录
          </el-button>
          <el-tag v-else type="success" effect="light">已保存正式PI</el-tag>
        </el-tooltip>
        <el-button type="primary" :icon="Wallet" @click="onAddPayment">添加付款</el-button>
        <el-button
          type="success"
          :icon="ShoppingCart"
          :disabled="selectedRows.length === 0 || !hasFormalRecord"
          @click="onPurchaseSelected"
        >
          采购选中 ({{ selectedRows.length }})
        </el-button>
        <el-button type="success" plain :icon="ShoppingCart" :disabled="!hasFormalRecord" @click="onPurchaseAll">采购全部</el-button>
        <el-button type="warning" :icon="Plus" @click="onSupplement">补充商品</el-button>
        <el-button type="info" :icon="Box" :disabled="!hasFormalRecord" @click="onBatchInbound">全部入库</el-button>
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
        :row-style="{ height: '80px' }"
        :cell-style="{ padding: '4px 0' }"
        :row-class-name="rowClassName"
        @selection-change="onSelectionChange"
        @row-contextmenu="onRowContextMenu"
        @cell-dblclick="onCellDblClick"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column label="导入序号" width="80" align="center" show-overflow-tooltip>
          <template #default="{ row, $index }">
            {{ displayImportSeq(row, $index) }}
          </template>
        </el-table-column>

        <!-- 锁定列：永不隐藏 -->
        <el-table-column prop="purchase_date" label="采购日期" width="140" show-overflow-tooltip v-if="colVisible['purchase_date']" />
        <el-table-column prop="product_code" label="编号备注" width="130" show-overflow-tooltip />
        <el-table-column prop="oe_number" label="OE号" width="120" show-overflow-tooltip v-if="colVisible['oe_number']" />
        <el-table-column prop="product_acquires" label="客户需求/产品备注" width="150" v-if="colVisible['remark']">
          <template #default="{ row }">
            <div class="product-name-lines" v-if="buildDisplayRemark(row.product_acquires, row.product_color).length">
              <div v-for="line in buildDisplayRemark(row.product_acquires, row.product_color)" :key="line" class="product-name-line">{{ line }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="product-name-lines" v-if="buildDisplayProductName(row.product_name, row.product_name_en).length">
              <div v-for="line in buildDisplayProductName(row.product_name, row.product_name_en)" :key="line" class="product-name-line">{{ line }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="image_url" label="图片" width="70" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              :src="assetUrl(row.image_url)"
              :preview-src-list="[assetUrl(row.image_url)]"
              :preview-teleported="true"
              fit="cover"
              style="width: 60px; height: 40px; border-radius: 2px; cursor: pointer"
            />
            <span v-else class="no-image">暂无</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_model" label="客户型号" width="130" show-overflow-tooltip v-if="colVisible['customer_model']" />
        <el-table-column prop="product_feature" label="产品特性" width="130" show-overflow-tooltip v-if="colVisible['product_feature']" />
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
        <el-table-column prop="latest_customer_reply" label="最新客户回复" width="140" show-overflow-tooltip v-if="colVisible['latest_customer_reply']" />
        <el-table-column prop="estimated_usd_price" label="预估美金报价" width="120" align="right" v-if="colVisible['estimated_usd_price']">
          <template #default="{ row }">
            {{ formatAmount(row.estimated_usd_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="estimated_margin" label="预估毛利率" width="100" align="right" v-if="colVisible['estimated_margin']">
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
        <el-table-column prop="factory_name" label="工厂简称" width="130" show-overflow-tooltip />
        <el-table-column prop="shop_url" label="店铺链接" width="120" show-overflow-tooltip v-if="colVisible['shop_url']">
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
        <el-table-column prop="delivery_date" label="交货日期" width="110" align="center" v-if="colVisible['delivery_date']">
          <template #default="{ row }">
            {{ formatDate(row.delivery_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="storage_status" label="是否已收货" width="100" align="center" v-if="colVisible['storage_status']">
          <template #default="{ row }">
            <el-tag v-if="row.storage_status === '已收货'" type="success" size="small">已收货</el-tag>
            <el-tag v-else-if="row.storage_status === '部分入库'" type="warning" size="small">部分入库</el-tag>
            <el-tag v-else type="info" size="small">未收货</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="factory_deposit" label="工厂订金" width="100" align="right" v-if="colVisible['factory_deposit']">
          <template #default="{ row }">
            {{ formatAmount(row.factory_deposit) }}
          </template>
        </el-table-column>
        <el-table-column prop="factory_balance" label="工厂尾款" width="100" align="right" v-if="colVisible['factory_balance']">
          <template #default="{ row }">
            {{ formatAmount(row.factory_balance) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock_in_action" label="入库操作" width="100" align="center" v-if="colVisible['stock_in_action']" />
        <el-table-column prop="stock_in_quantity" label="入库数量" width="90" align="right" v-if="colVisible['stock_in_quantity']" />
        <el-table-column prop="packaging" label="包装方式" width="110" show-overflow-tooltip v-if="colVisible['packaging']" />
        <el-table-column prop="purchase_option_name" label="采购选项/名称" width="140" show-overflow-tooltip v-if="colVisible['purchase_option_name']" />
        <el-table-column prop="product_detail" label="产品细节" width="150" show-overflow-tooltip v-if="colVisible['product_detail']" />
        <el-table-column prop="factory_code" label="工厂编号" width="120" show-overflow-tooltip v-if="colVisible['factory_code']" />
        <el-table-column prop="carton_size" label="纸箱尺寸" width="120" show-overflow-tooltip v-if="colVisible['carton_size']" />
        <el-table-column prop="pack_spec" label="打包规格" width="110" show-overflow-tooltip v-if="colVisible['pack_spec']" />
        <el-table-column prop="carton_count" label="箱数" width="80" align="right" v-if="colVisible['carton_count']" />
        <el-table-column prop="estimated_volume" label="预估体积(m³)" width="110" align="right">
          <template #default="{ row }">
            {{ row.estimated_volume ? row.estimated_volume.toFixed(4) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="carton_gross_weight" label="整箱毛重(kg)" width="110" align="right" v-if="colVisible['carton_gross_weight']">
          <template #default="{ row }">
            {{ row.carton_gross_weight ? row.carton_gross_weight.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_weight" label="总重量(kg)" width="110" align="right" v-if="colVisible['total_weight']">
          <template #default="{ row }">
            {{ row.total_weight ? row.total_weight.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="brand" label="品牌" width="100" show-overflow-tooltip v-if="colVisible['brand']" />
        <el-table-column prop="invoice_status" label="开票情况" width="100" show-overflow-tooltip />

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
              :class="{ danger: item.danger, disabled: isContextMenuItemDisabled(item.action) }"
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
    <PurchaseDialog ref="purchaseDialogRef" @success="onDetailSuccess" @purchase-complete="onPurchaseComplete" />
    <InboundDialog ref="inboundDialogRef" @success="onDetailSuccess" />
    <BatchInboundDialog ref="batchInboundDialogRef" @success="onDetailSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, reactive, watch } from 'vue'
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
  Setting,
} from '@element-plus/icons-vue'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'
import { orderSummaryApi } from '@/api/orderSummary'
import { nativeBridge } from '@/api/nativeBridge'
import { assetUrl } from '@/api/base'
import type { OrderDetailItem } from '@/types/orderSummary'
import {
  findDuplicates,
  isDuplicateIndex,
  type DuplicateGroup,
} from '@/utils/duplicateDetector'
import {
  applyStoredColumnVisibility as applyStoredColumnVisibilityUtil,
  enforceLockedColumnsVisible as enforceLockedColumnsVisibleUtil,
  getColumnVisibilityStorageKey as getColumnVisibilityStorageKeyUtil,
  LOCKED_COLUMNS,
  resetColumnVisibilityToDefault as resetColumnVisibilityToDefaultUtil,
  serializeColumnVisibility,
} from '@/utils/columnVisibility'
import {
  detectTemporaryPi,
  getFormalRecordTooltip,
  isFormalRecordRequiredAction,
} from '@/utils/formalRecord'
import {
  DEFAULT_IMPORT_FIELDS,
  autoMapImportColumns as autoMapImportColumnsUtil,
  buildDisplayProductName,
  buildDisplayRemark,
  buildImportItemFromRow,
} from '@/utils/orderImportMapping'
import PaymentDialog from '@/components/order/PaymentDialog.vue'
import SupplementDialog from '@/components/order/SupplementDialog.vue'
import ProductEditDialog from '@/components/order/ProductEditDialog.vue'
import PurchaseDialog from '@/components/order/PurchaseDialog.vue'
import InboundDialog from '@/components/order/InboundDialog.vue'
import BatchInboundDialog from '@/components/order/BatchInboundDialog.vue'
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
// 打开菜单后短时间内忽略关闭，避免同一次右键冒泡/全局监听立刻把菜单关掉
const contextMenuJustOpened = ref(false)
let contextMenuGuardTimer: number | null = null

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
const purchaseDialogRef = ref<InstanceType<typeof PurchaseDialog>>()
const inboundDialogRef = ref<InstanceType<typeof InboundDialog>>()
const batchInboundDialogRef = ref<InstanceType<typeof BatchInboundDialog>>()

// 多选 + 重复检测状态
const selectedRows = ref<OrderDetailItem[]>([])
const duplicateGroups = ref<DuplicateGroup[]>([])

const hasFormalRecord = ref(false)
const formalRecordLoading = ref(false)
const formalRecordSaving = ref(false)

// 列筛选状态：每个列独立开关
const colVisible = reactive<Record<string, boolean>>({
  purchase_date: true,
  product_code: true,
  oe_number: true,
  remark: true,
  product_name: true,
  image_url: true,
  customer_model: true,
  product_feature: true,
  quantity: true,
  unit_price: true,
  total_amount: true,
  latest_customer_reply: true,
  remaining_payment: true,
  estimated_usd_price: true,
  estimated_margin: true,
  purchase_price: true,
  shipping_fee: true,
  misc_fee: true,
  total_cost: true,
  factory_name: true,
  shop_url: true,
  delivery_date: true,
  storage_status: true,
  factory_deposit: true,
  factory_balance: true,
  stock_in_action: true,
  stock_in_quantity: true,
  packaging: true,
  purchase_option_name: true,
  product_detail: true,
  factory_code: true,
  carton_size: true,
  pack_spec: true,
  carton_count: true,
  estimated_volume: true,
  carton_gross_weight: true,
  total_weight: true,
  brand: true,
  invoice_status: true,
})

const lockedColumnSet = new Set(LOCKED_COLUMNS)

type ColumnVisibilityOption = {
  key: string
  label: string
  locked?: boolean
}

const columnVisibilityOptions: ColumnVisibilityOption[] = [
  { key: 'purchase_date', label: '采购日期' },
  { key: 'product_code', label: '客户产品编号', locked: true },
  { key: 'oe_number', label: 'OE号' },
  { key: 'remark', label: '客户需求/产品备注' },
  { key: 'product_name', label: '产品名称', locked: true },
  { key: 'image_url', label: '图片', locked: true },
  { key: 'customer_model', label: '客户型号' },
  { key: 'product_feature', label: '产品特性' },
  { key: 'quantity', label: '数量', locked: true },
  { key: 'unit_price', label: '报价', locked: true },
  { key: 'total_amount', label: '合计金额', locked: true },
  { key: 'latest_customer_reply', label: '最新客户回复' },
  { key: 'estimated_usd_price', label: '预估美金报价' },
  { key: 'estimated_margin', label: '预估毛利率' },
  { key: 'purchase_price', label: '采购价格', locked: true },
  { key: 'shipping_fee', label: '运费', locked: true },
  { key: 'misc_fee', label: '杂费', locked: true },
  { key: 'total_cost', label: '总金额(成本)', locked: true },
  { key: 'factory_name', label: '工厂简称', locked: true },
  { key: 'shop_url', label: '店铺链接' },
  { key: 'delivery_date', label: '交货日期' },
  { key: 'storage_status', label: '是否已收货' },
  { key: 'factory_deposit', label: '工厂订金' },
  { key: 'factory_balance', label: '工厂尾款' },
  { key: 'stock_in_action', label: '入库操作' },
  { key: 'stock_in_quantity', label: '入库数量' },
  { key: 'packaging', label: '包装方式' },
  { key: 'purchase_option_name', label: '采购选项/名称' },
  { key: 'product_detail', label: '产品细节' },
  { key: 'factory_code', label: '工厂编号' },
  { key: 'carton_size', label: '纸箱尺寸' },
  { key: 'pack_spec', label: '打包规格' },
  { key: 'carton_count', label: '箱数' },
  { key: 'estimated_volume', label: '预估体积', locked: true },
  { key: 'carton_gross_weight', label: '整箱毛重' },
  { key: 'total_weight', label: '总重量' },
  { key: 'brand', label: '品牌' },
  { key: 'invoice_status', label: '开票情况', locked: true },
]

function enforceLockedColumnsVisible() {
  Object.assign(colVisible, enforceLockedColumnsVisibleUtil(colVisible))
}

function getColumnVisibilityStorageKey() {
  return getColumnVisibilityStorageKeyUtil(store.currentOrder?.id)
}

function resetColumnVisibilityToDefault() {
  const defaults = resetColumnVisibilityToDefaultUtil(columnVisibilityOptions)
  Object.assign(colVisible, defaults)
}

function loadColumnVisibility() {
  const merged = applyStoredColumnVisibilityUtil(
    columnVisibilityOptions,
    localStorage.getItem(getColumnVisibilityStorageKey())
  )
  Object.assign(colVisible, merged)
}

function saveColumnVisibility() {
  localStorage.setItem(
    getColumnVisibilityStorageKey(),
    serializeColumnVisibility(columnVisibilityOptions, colVisible)
  )
}

async function loadFormalRecordStatus() {
  const orderId = store.currentOrder?.id
  hasFormalRecord.value = false
  if (!orderId) return

  formalRecordLoading.value = true
  try {
    const res = await orderSummaryApi.checkFormalRecord(orderId)
    hasFormalRecord.value = Boolean(res.data?.exists)
  } catch (error) {
    hasFormalRecord.value = false
  } finally {
    formalRecordLoading.value = false
  }
}

async function onSaveFormalRecord() {
  const orderId = store.currentOrder?.id
  if (!orderId) return

  try {
    await ElMessageBox.confirm(
      '确定将当前状态固化为正式纪录？保存后 PI 将锁定，可进行采购/入库操作。',
      '保存正式纪录',
      { type: 'warning' }
    )
  } catch {
    return
  }

  formalRecordSaving.value = true
  try {
    await orderSummaryApi.saveFormalRecord(orderId)
    hasFormalRecord.value = true
    ElMessage.success('正式纪录已保存，PI 已锁定，可进行采购/入库操作')
  } finally {
    formalRecordSaving.value = false
  }
}

function ensureFormalRecord(actionText = '采购/入库') {
  if (hasFormalRecord.value) return true
  ElMessage.warning(`请先点击「保存正式纪录」锁定PI后再${actionText}`)
  return false
}

function isFormalRecordRequiredActionInView(action: string) {
  return isFormalRecordRequiredAction(action)
}

function isContextMenuItemDisabled(action: string) {
  return isFormalRecordRequiredActionInView(action) && !hasFormalRecord.value
}

function getImportSeq(row: OrderDetailItem): number | null {
  const raw = (row as any).import_seq
  const seq = Number(raw)
  return Number.isFinite(seq) && seq > 0 ? seq : null
}

function displayImportSeq(row: OrderDetailItem, index: number) {
  return getImportSeq(row) ?? index + 1
}

function onRestoreImportOrder() {
  // 仅当存在有效导入序号时，按原始导入顺序恢复；无效序号保留在后面
  if (!store.detailItems.some(item => getImportSeq(item) !== null)) {
    ElMessage.info('当前数据没有导入序号，无需恢复顺序')
    return
  }
  const sorted = [...store.detailItems].sort((a, b) => {
    const seqA = getImportSeq(a) ?? Number.MAX_SAFE_INTEGER
    const seqB = getImportSeq(b) ?? Number.MAX_SAFE_INTEGER
    return seqA - seqB
  })
  store.$patch((state) => {
    ;(state as any).detailItems = sorted
  })
  ElMessage.success('已按导入序号恢复原始顺序')
}

const importFields = DEFAULT_IMPORT_FIELDS

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

const isTemporaryPi = computed(() => detectTemporaryPi(store.currentOrder?.pi_no))
const formalRecordTooltip = computed(() =>
  getFormalRecordTooltip(hasFormalRecord.value, isTemporaryPi.value)
)

const totalAmountSum = computed(() => {
  return store.detailItems.reduce((sum, item) => sum + (item.total_amount || 0), 0)
})

const totalStockInQuantity = computed(() => {
  return store.detailItems.reduce((sum, item) => sum + (item.stock_in_quantity || 0), 0)
})

onMounted(() => {
  loadColumnVisibility()
  loadFormalRecordStatus()
  document.addEventListener('click', hideContextMenu)
  // 仅在捕获阶段外监听左键关闭；右键关闭由 hideContextMenu 内部 guard 保护
  document.addEventListener('contextmenu', hideContextMenu)
})

watch(
  () => store.currentOrder?.id,
  () => {
    loadColumnVisibility()
    loadFormalRecordStatus()
  }
)

watch(
  colVisible,
  () => {
    enforceLockedColumnsVisible()
    saveColumnVisibility()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  document.removeEventListener('click', hideContextMenu)
  document.removeEventListener('contextmenu', hideContextMenu)
  if (contextMenuGuardTimer !== null) {
    window.clearTimeout(contextMenuGuardTimer)
    contextMenuGuardTimer = null
  }
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

  // 记录原始 Excel 行号（从 1 开始），用于恢复导入顺序
  data.forEach((row, idx) => {
    ;(row as any).__excel_row_index = idx + 1
  })

  importedRawData.value = data
  const headers = Object.keys(data[0])
  excelHeaders.value = headers

  autoMapColumns(headers)
  importDialogVisible.value = true
}

function autoMapColumns(headers: string[]) {
  const mapping = autoMapImportColumnsUtil(headers)
  for (const field of importFields) {
    columnMapping[field.key] = mapping[field.key] || ''
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

    const mappedItems = importedRawData.value.map((row, idx) =>
      buildImportItemFromRow(
        row,
        { ...columnMapping },
        (row as any).__excel_row_index ?? (idx + 1)
      )
    )

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
      采购日期: item.purchase_date,
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
  if (!ensureFormalRecord('采购')) return
  if (!store.currentOrder || store.detailItems.length === 0) {
    ElMessage.warning('当前订单无产品可采购')
    return
  }
  openPurchaseDialog(store.detailItems)
}

function onPurchaseSelected() {
  if (!ensureFormalRecord('采购')) return
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选要采购的产品')
    return
  }
  // 重复产品检测提示
  const selectedIds = new Set(selectedRows.value.map((r) => r.id))
  const selectedDuplicateGroups = duplicateGroups.value.filter((g) =>
    g.indices.some((i) => i < store.detailItems.length && selectedIds.has(store.detailItems[i]?.id))
  )
  if (selectedDuplicateGroups.length > 0) {
    const displays = selectedDuplicateGroups.map((g) => g.display)
    ElMessageBox.confirm(
      `选中产品中检测到 ${selectedDuplicateGroups.length} 组重复：\n${displays
        .slice(0, 10)
        .map((d) => `- ${d}`)
        .join('\n')}\n\n是否继续？`,
      '检测到重复产品',
      { type: 'warning', confirmButtonText: '继续采购', cancelButtonText: '取消' }
    )
      .then(() => openPurchaseDialog(selectedRows.value))
      .catch(() => {})
  } else {
    openPurchaseDialog(selectedRows.value)
  }
}

function openPurchaseDialog(items: OrderDetailItem[]) {
  if (!ensureFormalRecord('采购')) return
  if (!store.currentOrder) return
  // 提取预填的 1688 链接（key=product_id）
  const prefillUrls: Record<number, string[]> = {}
  // 用第一个产品的供应商信息预填弹窗
  let prefillShopName = ''
  let prefillLinkUrl = ''
  for (const it of items) {
    if (it.product_id && (it as any).shop_url) {
      prefillUrls[it.product_id] = [(it as any).shop_url]
    }
    // 优先用产品自身的供应商名称
    if (!prefillShopName && (it as any).supplier_name) {
      prefillShopName = (it as any).supplier_name
    }
    // 优先用产品自身的采购链接
    if (!prefillLinkUrl && (it as any).shop_url) {
      prefillLinkUrl = (it as any).shop_url
    }
  }
  // fallback 到 PI 级别的供应商名称
  if (!prefillShopName) {
    prefillShopName = (store.currentOrder as any).supplier_name || ''
  }
  purchaseDialogRef.value?.open(items, store.currentOrder.id, prefillUrls, prefillShopName, prefillLinkUrl)
}

function onSelectionChange(rows: OrderDetailItem[]) {
  selectedRows.value = rows
}

// 表格行 className：重复行高亮（浅黄背景）
function rowClassName({ row, rowIndex }: { row: OrderDetailItem; rowIndex: number }): string {
  if (isDuplicateIndex(rowIndex, duplicateGroups.value)) {
    return 'duplicate-row'
  }
  return ''
}

// 重新计算重复分组
function refreshDuplicates() {
  duplicateGroups.value = findDuplicates(store.detailItems)
}

// watch detailItems 变化时刷新重复检测
watch(
  () => store.detailItems,
  () => {
    refreshDuplicates()
    // 清空选中（避免引用失效的行）
    selectedRows.value = []
  },
  { deep: false, immediate: true }
)

function onBatchInbound() {
  if (!ensureFormalRecord('入库')) return
  if (!store.currentOrder || store.detailItems.length === 0) {
    ElMessage.warning('当前订单无产品可入库')
    return
  }
  batchInboundDialogRef.value?.open(store.detailItems, store.currentOrder.id)
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

function onPurchaseComplete(payload: { factory_name: string; shop_url: string; wechatId: string; wechatNickname: string }) {
  store.detailItems.forEach((item) => {
    if (payload.factory_name) {
      ;(item as any).supplier_name = payload.factory_name
    }
    if (payload.shop_url) {
      ;(item as any).shop_url = payload.shop_url
    }
  })
  if (store.currentOrder?.id) {
    store.fetchOrderDetail(store.currentOrder.id)
  }
}

function onRowContextMenu(row: OrderDetailItem, _column: any, event: MouseEvent) {
  // el-table row-contextmenu 事件签名: (row, column, event)
  if (!event || typeof event.preventDefault !== 'function') {
    return
  }
  event.preventDefault()
  // 阻止冒泡到 document，避免 onMounted 里的 contextmenu 监听器立刻关闭菜单
  event.stopPropagation()
  currentContextRow.value = row
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
  contextMenuJustOpened.value = true
  if (contextMenuGuardTimer !== null) {
    window.clearTimeout(contextMenuGuardTimer)
  }
  contextMenuGuardTimer = window.setTimeout(() => {
    contextMenuJustOpened.value = false
    contextMenuGuardTimer = null
  }, 0)
}

function hideContextMenu() {
  // 同一次右键事件触发的关闭请求忽略，确保菜单能显示出来
  if (contextMenuJustOpened.value) {
    return
  }
  contextMenuVisible.value = false
  currentContextRow.value = null
}

async function handleContextMenuAction(action: string) {
  const item = currentContextRow.value
  if (!item) return
  hideContextMenu()
  if (isFormalRecordRequiredActionInView(action) && !ensureFormalRecord(action === 'stockIn' ? '入库' : '采购')) return
  
  switch (action) {
    case 'purchase':
    case 'repurchase':
      // 单品采购
      if (action === 'repurchase') {
        await ElMessageBox.confirm(
          `产品「${item.product_name}」已采购过，确定要重新采购？`,
          '确认重新采购',
          { type: 'warning' }
        )
      }
      purchaseDialogRef.value?.open(
        [item],
        store.currentOrder?.id!,
        item.product_id && (item as any).shop_url
          ? { [item.product_id]: [(item as any).shop_url] }
          : {},
        (item as any).supplier_name || (store.currentOrder as any).supplier_name || '',
        (item as any).shop_url || ''
      )
      break
    case 'stockIn':
      // 单品入库
      inboundDialogRef.value?.open(item)
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
/* 重复产品行：浅黄背景 */
:deep(.el-table .duplicate-row) {
  background-color: #fef3c7 !important;
}

:deep(.el-table .duplicate-row td) {
  background-color: #fef3c7 !important;
}

/* 列筛选面板 */
.col-filter-panel {
  user-select: none;
}

.col-filter-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: 600;
}

.col-filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px 8px;
  max-height: 400px;
  overflow-y: auto;
}

.col-filter-grid :deep(.el-checkbox) {
  display: flex;
  margin-bottom: 4px;
  font-size: 13px;
  white-space: nowrap;
}

.col-filter-grid :deep(.el-checkbox__label) {
  font-size: 13px;
}

/* 重复行 hover */
:deep(.el-table .duplicate-row:hover > td) {
  background-color: #fde68a !important;
}

.product-name-lines {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 18px;
  white-space: normal;
}

.product-name-line {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

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

.context-menu-item.disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

.context-menu-item.disabled:hover {
  background-color: transparent;
  color: #9ca3af;
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

