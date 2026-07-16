<template>
  <el-dialog
    v-model="visible"
    title="新增订单"
    width="900px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <!-- 客户选择（必选，所有模式共享） -->
    <el-form label-width="100px" :inline="false">
      <el-form-item label="客户" required>
        <el-select
          v-model="form.customer_id"
          filterable
          remote
          :remote-method="searchCustomers"
          :loading="customerLoading"
          placeholder="请输入客户名称/编号/区域搜索"
          style="width: calc(100% - 110px)"
          @change="onCustomerChange"
        >
          <el-option
            v-for="c in customers"
            :key="c.id"
            :label="c.customer_name"
            :value="c.id"
          >
            <div class="customer-option">
              <span class="customer-name">{{ c.customer_name }}</span>
              <span v-if="c.customer_code" class="customer-code">[{{ c.customer_code }}]</span>
              <span v-if="c.country" class="customer-country">{{ c.country }}</span>
            </div>
          </el-option>
          <template #empty>
            <div class="customer-empty">
              <div v-if="customerSearchQuery">未找到客户「{{ customerSearchQuery }}」</div>
              <div v-else>暂无客户数据</div>
              <el-button
                v-if="customerSearchQuery"
                type="primary"
                size="small"
                link
                @click="openNewCustomerDialog"
              >
                + 新建客户
              </el-button>
            </div>
          </template>
        </el-select>
        <el-button
          type="primary"
          size="small"
          link
          @click="openNewCustomerDialog"
        >
          + 新建客户
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 新建客户子对话框 -->
    <el-dialog
      v-model="newCustomerDialogVisible"
      title="新建客户"
      width="500px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form ref="newCustomerFormRef" :model="newCustomer" :rules="newCustomerRules" label-width="100px">
        <el-form-item label="客户编号">
          <el-input v-model="newCustomer.customer_code" placeholder="可选，系统可自动生成" />
        </el-form-item>
        <el-form-item label="客户名称 *" prop="customer_name">
          <el-input v-model="newCustomer.customer_name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="国家/区域">
          <el-input v-model="newCustomer.country" placeholder="可选" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="newCustomer.contact_person" placeholder="可选" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="newCustomer.phone" placeholder="可选" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="newCustomer.email" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="newCustomer.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newCustomerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingCustomer" @click="submitNewCustomer">确定新建</el-button>
      </template>
    </el-dialog>

    <el-tabs v-model="activeTab" class="new-order-tabs">
      <!-- Excel 导入（默认） -->
      <el-tab-pane label="Excel 导入（推荐）" name="excel">
        <div v-if="!form.customer_id" class="tip-warn">
          <el-alert type="info" :closable="false" show-icon>
            请先选择客户
          </el-alert>
        </div>

        <!-- 上传区 -->
        <el-upload
          v-if="form.customer_id"
          ref="uploadRef"
          class="excel-uploader"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :on-exceed="onFileExceed"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 Excel 文件拖到此处，或<em>点击选择文件</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx / .xls 格式；第一行需为表头；整个 Excel 将作为一个新订单的明细行导入
            </div>
          </template>
        </el-upload>

        <!-- 已上传：字段匹配 + 预览 -->
        <template v-if="excelData.length > 0">
          <el-divider content-position="left">字段匹配</el-divider>
          <div class="mapping-tip">
            <el-icon><info-filled /></el-icon>
            <span>请确认 Excel 列与系统字段的对应关系。最小必填：<b style="color:#f56c6c">客户型号</b> + <b style="color:#f56c6c">数量</b>（OE号、单价等可选，缺失可勾选"保留不完整行"）</span>
          </div>

          <el-form :model="columnMapping" label-width="120px" class="mapping-form">
            <el-row :gutter="12">
              <el-col :span="8" v-for="field in mappingFields" :key="field.key">
                <el-form-item :label="field.label">
                  <el-select
                    v-model="columnMapping[field.key]"
                    :placeholder="field.required ? '必选' : '可选'"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="h in availableHeadersForField(field.key)"
                      :key="h"
                      :label="h"
                      :value="h"
                    />
                  </el-select>
                  <template v-if="columnMapping[field.key]" #label>
                    <span style="color: #67c23a;">{{ field.label }} ✓</span>
                  </template>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <!--预设内容 -->
          <div class="preset-content">
            <span>毛利率：</span>
            <el-input-number v-model="presetProfitMargin" :min="0" :max="100" :controls="false" style="width: 100px;" />
            <span style="margin-left: 16px;">汇率：</span>
            <el-input-number v-model="presetExchangeRate" :min="0" :precision="2" :controls="false" style="width: 100px;" />
          </div>

          <el-divider content-position="left">
            数据预览（共 {{ excelData.length }} 行）
          </el-divider>

          <el-table :data="previewData" stripe size="small" max-height="320" border>
            <el-table-column type="index" label="#" width="50" fixed />
            <el-table-column
              v-for="h in excelHeaders.slice(0, 8)"
              :key="h"
              :prop="h"
              :label="h"
              min-width="120"
              show-overflow-tooltip
            />
            <el-table-column v-if="excelHeaders.length > 8" label="..." width="60" align="center" />
          </el-table>

          <!-- 校验提示 -->
          <div class="validation-bar">
            <el-tag v-if="excelData.length === 0" type="info">未导入数据</el-tag>
            <template v-else>
              <el-tag v-if="incompleteRowCount === 0" type="success">
                全部 {{ excelData.length }} 行可导入
              </el-tag>
              <template v-else>
                <el-tag type="success">{{ validRowCount }} 行可导入</el-tag>
                <el-tag type="danger">{{ incompleteRowCount }} 行不完整（缺客户产品编号/数量）</el-tag>
              </template>
            </template>
            <el-checkbox v-model="keepIncomplete" :disabled="incompleteRowCount === 0">
              保留不完整行
            </el-checkbox>
            <el-button v-if="excelData.length" link type="primary" @click="downloadTemplate">
              <el-icon><download /></el-icon>
              下载导入模板
            </el-button>
          </div>

          <!-- 错误明细 -->
          <el-collapse v-if="validationErrors.length" v-model="errorPanelOpen" class="error-collapse">
            <el-collapse-item :title="`查看不完整的行（${validationErrors.length}）`" name="errors">
              <el-table :data="validationErrors" size="small" max-height="240">
                <el-table-column prop="row" label="行号" width="70" />
                <el-table-column prop="message" label="原因" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </template>
      </el-tab-pane>

      <!-- 单条新增（备选） -->
      <el-tab-pane label="单条新增" name="single">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
          <el-form-item label="搜索模式">
            <el-radio-group v-model="searchMode">
              <el-radio value="both">OE号 + 名称</el-radio>
              <el-radio value="oe">仅OE号</el-radio>
              <el-radio value="name">仅名称</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="产品搜索" prop="search_keyword">
            <el-autocomplete
              v-model="searchKeyword"
              :fetch-suggestions="searchProducts"
              placeholder="输入关键词搜索产品..."
              :trigger-on-focus="false"
              clearable
              style="width: 100%"
              @select="onProductSelect"
              @change="onSearchChange"
            >
              <template #prefix>
                <el-icon><search /></el-icon>
              </template>
              <template #default="{ item }">
                <div class="product-suggestion">
                  <span class="oe">{{ item.oe_number || item.oe || '-' }}</span>
                  <span class="name">{{ item.detail_desc || item.product_name || item.customer_model || '-' }}</span>
                </div>
              </template>
            </el-autocomplete>
          </el-form-item>

          <el-form-item label="搜索结果">
            <el-select
              v-model="selectedProductIndex"
              placeholder="请选择搜索到的产品"
              style="width: 100%"
              @change="onResultSelect"
            >
              <el-option
                v-for="(p, idx) in searchResults"
                :key="idx"
                :label="formatProductDisplay(p)"
                :value="idx"
              />
            </el-select>
          </el-form-item>

          <template v-if="selectedProduct">
            <el-divider content-position="left">已选产品</el-divider>
            <div class="selected-product-info">
              <el-tag type="success">{{ formatProductDisplay(selectedProduct) }}</el-tag>
            </div>
          </template>

          <el-divider content-position="left">产品信息</el-divider>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="客户型号" prop="customer_code">
                <el-input v-model="form.customer_code" placeholder="客户型号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Model">
                <el-input v-model="form.customer_model" placeholder="Model / 客户型号" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="OE号" prop="oe_number">
            <el-input v-model="form.oe_number" placeholder="OE号" />
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="数量" prop="quantity">
                <el-input-number v-model="form.quantity" :min="1" :max="999999" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="单价(USD)" prop="unit_price">
                <el-input-number v-model="form.unit_price" :min="0.01" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="合计金额">
                <div class="amount-label">$ {{ formatAmount(totalAmount) }}</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="onClose">取消</el-button>
        <el-button
          v-if="activeTab === 'excel'"
          type="success"
          :loading="submitting"
          :disabled="!canSubmitExcel"
          @click="onSubmitExcel"
        >
          导入并创建订单（{{ importRowCount }} 行）
        </el-button>
        <el-button
          v-else
          type="success"
          :loading="submitting"
          @click="onSubmitSingle"
        >
          保存
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Search, UploadFilled, InfoFilled, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import type { UploadFile, UploadRawFile, UploadInstance } from 'element-plus'
import { apiUrl } from '@/api/base'
import { CUSTOMERS, ORDERS_BFF, PI, PRODUCT_CUSTOMER } from '@/api/endpoints'

interface Customer {
  id: number
  customer_code?: string
  customer_name: string
  country?: string
  contact_person?: string
}

interface Product {
  id?: number
  product_id?: number
  oe_number?: string
  oe?: string
  detail_desc?: string
  product_name?: string
  customer_model?: string
  customer_code?: string
  product_code?: string
  unit_price?: number
  price?: number
  price_usd?: number
}

interface ValidationError {
  row: number
  message: string
}

// 与后端 schemas/order_import.py EXCEL_HEADER_MAPPING 对齐
const FIELD_KEYS = [
  'customer_code',   // 客户产品编号
  'oe_number',       // OE号
  'product_desc',    // 产品描述
  'detail_desc',     // 产品名称
  'product_feature', // 产品特性
  'quantity',        // 数量
  'unit_price',      // 单价
] as const

const mappingFields: Array<{ key: string; label: string; required: boolean }> = [
  { key: 'customer_code',   label: '客户型号', required: true },
  { key: 'oe_number',       label: 'OE号',         required: false },
  { key: 'quantity',        label: '数量',         required: true },
  { key: 'unit_price',      label: '单价',         required: false },
  { key: 'detail_desc',     label: '产品名称',     required: false },
  { key: 'product_desc',    label: '产品描述',     required: false },
]

const visible = ref(false)
const submitting = ref(false)
const activeTab = ref<'excel' | 'single'>('excel')

const formRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()
const customers = ref<Customer[]>([])

const searchMode = ref<'both' | 'oe' | 'name'>('both')
const searchKeyword = ref('')
const searchResults = ref<Product[]>([])
const selectedProductIndex = ref<number | null>(null)
const selectedProduct = ref<Product | null>(null)

const form = reactive({
  customer_id: null as number | null,
  customer_code: '',
  customer_model: '',
  oe_number: '',
  quantity: 1,
  unit_price: 0,
})

const rules: FormRules = {
  customer_code: [{ required: true, message: '请输入客户产品编号', trigger: 'blur' }],
  oe_number: [{ required: true, message: '请输入OE号', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
}

const totalAmount = computed(() => form.quantity * form.unit_price)

// ============== Excel 状态 ==============
const excelData = ref<any[]>([])
const excelHeaders = ref<string[]>([])
const errorPanelOpen = ref<string[]>([])

const columnMapping = reactive<Record<string, string>>(
  Object.fromEntries(FIELD_KEYS.map(k => [k, '']))
)

const keepIncomplete = ref(false) // 是否保留不完整行（缺客户产品编号/数量）
const presetProfitMargin = ref(25)
const presetExchangeRate = ref(6.8)

const previewData = computed(() => excelData.value)

const getVal = (row: any, key: string): any => {
  const col = columnMapping[key]
  if (!col) return undefined
  return row?.[col]
}

const isValidRow = (row: any): boolean => {
  // 最小必填：客户产品编号 + 数量（与 PyQt order_import_dialog 旧逻辑一致）
  const code = getVal(row, 'customer_code')
  const qty = getVal(row, 'quantity')
  return (
    code && String(code).trim() !== '' &&
    qty !== undefined && qty !== null && String(qty).trim() !== '' && !isNaN(Number(qty)) && Number(qty) > 0
  )
}

// 下拉框候选：排除已被其他字段占用的列，但保留当前字段已选中的列
const availableHeadersForField = (fieldKey: string): string[] => {
  const usedByOthers = new Set<string>()
  for (const [key, col] of Object.entries(columnMapping)) {
    if (key !== fieldKey && col) {
      usedByOthers.add(col)
    }
  }
  return excelHeaders.value.filter(h => !usedByOthers.has(h))
}

const validRowCount = computed(() => {
  if (!excelData.value.length) return 0
  return excelData.value.filter(isValidRow).length
})

const incompleteRowCount = computed(() => {
  if (!excelData.value.length) return 0
  return excelData.value.filter(row => !isValidRow(row)).length
})

// 实际要导入的行数：默认仅 valid；勾选"保留不完整行"后包含 incomplete
const importRowCount = computed(() => {
  if (keepIncomplete.value) return excelData.value.length
  return validRowCount.value
})

const canSubmitExcel = computed(() => {
  if (!form.customer_id) return false
  if (excelData.value.length === 0) return false
  // 必须先映射"客户产品编号"和"数量"两列
  if (!columnMapping.customer_code || !columnMapping.quantity) return false
  return importRowCount.value > 0
})

const validationErrors = computed<ValidationError[]>(() => {
  if (!excelData.value.length) return []
  const errs: ValidationError[] = []
  excelData.value.forEach((row, idx) => {
    const rowNo = idx + 2 // 1 是表头
    const code = getVal(row, 'customer_code')
    const qty = getVal(row, 'quantity')
    const missing: string[] = []
    if (!code || !String(code).trim()) missing.push('客户产品编号')
    if (qty === undefined || qty === null || String(qty).trim() === '' || isNaN(Number(qty)) || Number(qty) <= 0) {
      missing.push('数量')
    }
    if (missing.length) {
      errs.push({ row: rowNo, message: `缺少或无效：${missing.join('、')}` })
    }
  })
  return errs
})

const emit = defineEmits<{
  (e: 'success', payload: { orderId: number; count: number } | number): void
}>()

function formatAmount(amount: number): string {
  return isNaN(amount) ? '0.00' : amount.toFixed(2)
}

function formatProductDisplay(p: Product): string {
  const oe = p.oe_number || p.oe || ''
  const name = p.detail_desc || p.product_name || p.customer_model || ''
  if (oe && name) return `${oe} - ${name}`
  return oe || name || '未命名产品'
}

// ============== 客户相关 ==============
const customerLoading = ref(false)
const customerSearchQuery = ref('')
const newCustomerDialogVisible = ref(false)
const newCustomerFormRef = ref<FormInstance>()
const creatingCustomer = ref(false)

const newCustomer = reactive({
  customer_code: '',
  customer_name: '',
  country: '',
  contact_person: '',
  phone: '',
  email: '',
  remark: '',
})

const newCustomerRules: FormRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
}

async function loadCustomers() {
  customerLoading.value = true
  try {
    const res = await fetch(apiUrl(`${CUSTOMERS.search}?keyword=&limit=200`))
    if (res.ok) {
      const data = await res.json()
      const list = Array.isArray(data) ? data : (data.list || data.data || [])
      customers.value = list.map((c: any) => ({
        id: c.id,
        customer_code: c.customer_code || '',
        customer_name: c.customer_name || c.name || '',
        country: c.country || '',
      }))
    }
  } catch (e) {
    console.error('Failed to load customers:', e)
    ElMessage.error('加载客户列表失败')
  } finally {
    customerLoading.value = false
  }
}

let customerSearchTimer: ReturnType<typeof setTimeout> | null = null

async function searchCustomers(query: string) {
  customerSearchQuery.value = query || ''
  if (customerSearchTimer) clearTimeout(customerSearchTimer)
  customerSearchTimer = setTimeout(async () => {
    customerLoading.value = true
    try {
      const url = apiUrl(`${CUSTOMERS.search}?keyword=${encodeURIComponent(query || '')}&limit=200`)
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        const list = Array.isArray(data) ? data : (data.list || data.data || [])
        customers.value = list.map((c: any) => ({
          id: c.id,
          customer_code: c.customer_code || '',
          customer_name: c.customer_name || c.name || '',
          country: c.country || '',
        }))
      }
    } catch (e) {
      console.error('搜索客户失败:', e)
    } finally {
      customerLoading.value = false
    }
  }, 200)
}

function openNewCustomerDialog() {
  // 预填名称（如果有搜索词）
  if (customerSearchQuery.value && !newCustomer.customer_name) {
    newCustomer.customer_name = customerSearchQuery.value
  }
  newCustomerDialogVisible.value = true
}

async function submitNewCustomer() {
  if (!newCustomerFormRef.value) return
  await newCustomerFormRef.value.validate(async (valid) => {
    if (!valid) return
    creatingCustomer.value = true
    try {
      const payload = {
        dept_id: 'S',
        customer_name: newCustomer.customer_name,
        customer_code: newCustomer.customer_code || undefined,
        country: newCustomer.country || undefined,
        contact_person: newCustomer.contact_person || undefined,
        phone: newCustomer.phone || undefined,
        email: newCustomer.email || undefined,
        remark: newCustomer.remark || undefined,
      }
      const res = await fetch(apiUrl(CUSTOMERS.create), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        const data = await res.json()
        ElMessage.success('客户创建成功')
        // 添加到下拉列表并选中
        const newCust: Customer = {
          id: data.id,
          customer_code: data.customer_code || newCustomer.customer_code || '',
          customer_name: data.customer_name || newCustomer.customer_name,
        }
        customers.value.unshift(newCust)
        form.customer_id = newCust.id
        newCustomerDialogVisible.value = false
        // 重置新建客户表单
        newCustomer.customer_code = ''
        newCustomer.customer_name = ''
        newCustomer.country = ''
        newCustomer.contact_person = ''
        newCustomer.phone = ''
        newCustomer.email = ''
        newCustomer.remark = ''
      } else {
        const err = await res.json().catch(() => ({}))
        ElMessage.error(err.detail || err.message || '创建客户失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '创建客户失败')
    } finally {
      creatingCustomer.value = false
    }
  })
}

function onCustomerChange() {
  searchKeyword.value = ''
  searchResults.value = []
  selectedProductIndex.value = null
  selectedProduct.value = null
}

// ============== 单条搜索 ==============
let searchTimer: ReturnType<typeof setTimeout> | null = null

async function searchProducts(query: string, callback: (results: Product[]) => void) {
  if (searchTimer) clearTimeout(searchTimer)
  if (!query || query.length < 2) {
    callback([])
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      let url = apiUrl(`${PRODUCT_CUSTOMER.search}?keyword=${encodeURIComponent(query)}&limit=20`)
      if (searchMode.value !== 'both') {
        url += `&fields=${searchMode.value}`
      }
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        const results = data.results || data.data || data || []
        searchResults.value = Array.isArray(results) ? results : []
        callback(searchResults.value)
      } else {
        searchResults.value = []
        callback([])
      }
    } catch {
      searchResults.value = []
      callback([])
    }
  }, 150)
}

function onSearchChange() {
  selectedProductIndex.value = null
  selectedProduct.value = null
}

function onResultSelect(index: number) {
  if (index < 0 || index >= searchResults.value.length) {
    selectedProduct.value = null
    return
  }
  const product = searchResults.value[index]
  selectedProduct.value = product
  form.customer_code = product.customer_code || product.product_code || ''
  form.customer_model = product.customer_model || ''
  form.oe_number = product.oe_number || product.oe || ''
  const price = product.price_usd || product.price || product.unit_price || 0
  form.unit_price = price
}

function onProductSelect(product: Product) {
  const idx = searchResults.value.findIndex(
    p => p.id === product.id || p.product_id === product.product_id
  )
  if (idx >= 0) {
    selectedProductIndex.value = idx
    onResultSelect(idx)
  }
}

// ============== Excel 解析 ==============
function onFileExceed() {
  ElMessage.warning('仅支持上传一个文件，请先移除现有文件')
}

function onFileChange(file: UploadFile) {
  const raw = file.raw as UploadRawFile | undefined
  if (!raw) {
    ElMessage.error('读取文件失败')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const result = e.target?.result
      if (!result) {
        ElMessage.error('读取文件失败')
        return
      }
      const data = new Uint8Array(result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData: any[][] = XLSX.utils.sheet_to_json(firstSheet, { header: 1, defval: '' })
      if (!jsonData.length) {
        ElMessage.warning('Excel 文件为空')
        return
      }
      const rawHeaders = (jsonData[0] as any[]).map(h => String(h ?? '').trim())
      const headers = rawHeaders.filter(h => h !== '')
      const headerIndexMap: Record<string, number> = {}
      rawHeaders.forEach((h, i) => { headerIndexMap[h] = i })
      const dataRows = jsonData.slice(1).filter(row =>
        row.some(c => c !== '' && c !== null && c !== undefined)
      )
      excelHeaders.value = headers
      excelData.value = dataRows.map(row => {
        const obj: Record<string, any> = {}
        headers.forEach(h => {
          obj[h] = row[headerIndexMap[h]]
        })
        return obj
      })

      // 重置映射
      FIELD_KEYS.forEach(k => { columnMapping[k] = '' })
      autoMatchColumns()
      errorPanelOpen.value = []

      if (excelData.value.length === 0) {
        ElMessage.warning('Excel 中没有有效数据行')
      } else {
        ElMessage.success(`已读取 ${excelData.value.length} 行数据`)
      }
    } catch (err) {
      console.error(err)
      ElMessage.error('读取 Excel 文件失败')
      excelData.value = []
      excelHeaders.value = []
    }
  }
  reader.readAsArrayBuffer(raw)
}

function onFileRemove() {
  excelData.value = []
  excelHeaders.value = []
  FIELD_KEYS.forEach(k => { columnMapping[k] = '' })
  errorPanelOpen.value = []
}

function autoMatchColumns() {
  // 关键词表 - 与后端 EXCEL_HEADER_MAPPING 的中文表头对齐
  const map: Record<string, string[]> = {
    customer_code: ['客户产品编号', '客户型号', '客户型号(Model)', '编号', 'Model', 'MODEL'],
    oe_number: ['OE号', 'OE', 'oe'],
    quantity: ['数量', 'QTY', 'Quantity', 'qty'],
    unit_price: ['单价', '报价', 'price', 'PRICE', '报价(USD/RMB)'],
    detail_desc: ['产品名称', '名称', '产品描述', '描述'],
    product_desc: ['产品描述', '描述', 'description'],
    product_feature: ['产品特性', '特性', 'feature'],
  }
  for (const key of FIELD_KEYS) {
    const kws = map[key] || []
    for (const header of excelHeaders.value) {
      const h = String(header).toLowerCase().trim()
      if (kws.some(k => h === k.toLowerCase() || h.includes(k.toLowerCase()))) {
        columnMapping[key] = header
        break
      }
    }
  }
}

function downloadTemplate() {
  const headers = [
    '客户产品编号', 'OE号', '产品名称', '产品特性',
    '数量', '单价'
  ]
  const example = [
    headers,
    ['CUST-001', '04465-30320', '刹车片 Front Brake Pad', '陶瓷 Ceramic', 50, 12.5],
    ['CUST-002', '04465-30350', '刹车片 Rear Brake Pad',  '陶瓷 Ceramic', 30, 11.8],
  ]
  const ws = XLSX.utils.aoa_to_sheet(example)
  ws['!cols'] = headers.map(() => ({ wch: 18 }))
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '订单模板')
  XLSX.writeFile(wb, '订单导入模板.xlsx')
}

// ============== 提交 ==============
async function onSubmitSingle() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!form.customer_id) {
      ElMessage.warning('请选择客户')
      return
    }
    if (!form.customer_code) {
      ElMessage.warning('请输入客户产品编号')
      return
    }
    if (!form.oe_number) {
      ElMessage.warning('请输入OE号')
      return
    }
    if (!selectedProduct.value && (form.customer_model || form.customer_code)) {
      try {
        await ElMessageBox.confirm(
          '未匹配到已有产品，是否继续添加新商品？',
          '未匹配到产品',
          { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
        )
      } catch {
        return
      }
    }
    submitting.value = true
    try {
      const payload = {
        dept_id: 'S',
        customer_id: form.customer_id,
        items: [{
          quantity: form.quantity,
          unit_price: form.unit_price,
          customer_code: form.customer_code,
          customer_model: form.customer_model || undefined,
          oe_number: form.oe_number || undefined,
        }],
        payment_stages: [],
      }
      const res = await fetch(apiUrl(PI.create), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        const data = await res.json()
        ElMessage.success('订单创建成功')
        emit('success', { orderId: data.id, count: 1 })
        onClose()
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || err.message || '创建失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '创建订单失败')
    } finally {
      submitting.value = false
    }
  })
}

async function onSubmitExcel() {
  if (!canSubmitExcel.value) {
    ElMessage.warning('请检查客户、文件与必填字段映射')
    return
  }

  // 计算待提交的行
  const rowsToImport = keepIncomplete.value
    ? [...excelData.value]
    : excelData.value.filter(isValidRow)

  if (rowsToImport.length === 0) {
    ElMessage.warning('没有可导入的行')
    return
  }

  if (incompleteRowCount.value > 0) {
    try {
      await ElMessageBox.confirm(
        keepIncomplete.value
          ? `本次将导入全部 ${rowsToImport.length} 行（包含 ${incompleteRowCount.value} 行不完整数据）。是否继续？`
          : `检测到 ${incompleteRowCount.value} 行不完整（缺客户产品编号/数量），将被跳过。是否继续导入剩余 ${rowsToImport.length} 行？`,
        '确认导入',
        {
          confirmButtonText: '继续导入',
          cancelButtonText: '取消',
          type: keepIncomplete.value ? 'warning' : 'info',
        }
      )
    } catch {
      return
    }
  }

  submitting.value = true
  try {
    // 重建 Excel：表头替换为系统字段名（中文），数据按字段映射重排。
    // 后端 EXCEL_HEADER_MAPPING 只认中文表头，例如 '客户产品编号' -> customer_code。
    const systemFieldName: Record<string, string> = {
      customer_code: '客户产品编号',
      oe_number: 'OE号',
      detail_desc: '产品名称',
      product_desc: '产品描述',
      product_feature: '产品特性',
      quantity: '数量',
      unit_price: '单价',
      company_code: '我司产编号',
    }
    const usedFieldToExcelCol: Record<string, string> = {}
    for (const [field, col] of Object.entries(columnMapping)) {
      if (col && systemFieldName[field]) {
        usedFieldToExcelCol[systemFieldName[field]] = col
      }
    }
    const outHeaders = Object.keys(usedFieldToExcelCol)
    const customerCodeCol = columnMapping['customer_code']
    const outRows = rowsToImport.map(row => {
      const obj: Record<string, any> = {}
      for (const [sysName, col] of Object.entries(usedFieldToExcelCol)) {
        obj[sysName] = row[col]
      }
      // 我司产编号默认等于客户产品编号
      if (!obj['我司产编号'] && customerCodeCol) {
        obj['我司产编号'] = row[customerCodeCol] || ''
      }
      return obj
    })

    const ws = XLSX.utils.json_to_sheet(outRows, { header: outHeaders })
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '订单')
    const arrayBuf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
    const blob = new Blob([arrayBuf], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const file = new File([blob], 'order_import.xlsx', { type: blob.type })
    const fd = new FormData()
    fd.append('file', file)

    let query = `auto_match=true`
    if (form.customer_id) query += `&customer_id=${form.customer_id}`
    query += `&profit_margin=${presetProfitMargin.value}&exchange_rate=${presetExchangeRate.value}`

    const res = await fetch(apiUrl(ORDERS_BFF.import + '?' + query), {
      method: 'POST',
      body: fd,
    })
    const data = await res.json()
    if (res.ok && data.success) {
      const orderId = (data.created_orders && data.created_orders[0]) || data.order_id || data.id
      const count = data.success_count || outRows.length
      const failed = data.failed_count || 0
      let msg = `导入完成：成功 ${count} 条`
      if (failed > 0) msg += `，失败 ${failed} 条`
      if (orderId) msg += `，订单 #${orderId}`
      ElMessage.success(msg)
      emit('success', { orderId, count })
      onClose()
    } else {
      const errMsg = (data.errors && data.errors[0] && data.errors[0].error) || ''
      const msg = data.detail || data.message || errMsg || `导入失败（${data.failed_count || 0} 行失败）`
      ElMessage.error(msg)
    }
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.message || '导入失败')
  } finally {
    submitting.value = false
  }
}

function resetAll() {
  form.customer_id = null
  form.customer_code = ''
  form.customer_model = ''
  form.oe_number = ''
  form.quantity = 1
  form.unit_price = 0
  searchKeyword.value = ''
  searchResults.value = []
  selectedProductIndex.value = null
  selectedProduct.value = null
  excelData.value = []
  excelHeaders.value = []
  FIELD_KEYS.forEach(k => { columnMapping[k] = '' })
  errorPanelOpen.value = []
  keepIncomplete.value = false
  activeTab.value = 'excel'
  uploadRef.value?.clearFiles()
}

function onClose() {
  visible.value = false
}

function open() {
  resetAll()
  visible.value = true
  loadCustomers()
}

defineExpose({ open })
</script>

<style scoped>
.amount-label {
  font-size: 18px;
  font-weight: bold;
  color: #67c23a;
  line-height: 32px;
}
.selected-product-info {
  margin-bottom: 16px;
}
.product-suggestion {
  display: flex;
  gap: 12px;
  line-height: 1.5;
}
.product-suggestion .oe {
  color: #909399;
  font-size: 12px;
  min-width: 120px;
}
.product-suggestion .name {
  flex: 1;
}

.new-order-tabs {
  margin-top: -8px;
}
.new-order-tabs :deep(.el-tabs__header) {
  margin-bottom: 12px;
}
.tip-warn {
  margin-bottom: 12px;
}
.excel-uploader {
  width: 100%;
}
.excel-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 28px 16px;
}
.mapping-form {
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px 16px 0;
  margin-bottom: 12px;
}
.mapping-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}
.validation-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.error-collapse {
  margin-top: 12px;
}
.customer-option {
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.5;
}
.customer-option .customer-name {
  font-weight: 500;
  color: #1f2937;
}
.customer-option .customer-code {
  color: #909399;
  font-size: 12px;
}
.customer-option .customer-country {
  margin-left: auto;
  color: #67c23a;
  font-size: 12px;
  background: #f0f9eb;
  padding: 1px 6px;
  border-radius: 3px;
}
.customer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  color: #909399;
  font-size: 12px;
}
</style>
