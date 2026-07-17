<template>
  <el-dialog
    v-model="visible"
    title="补充商品"
    width="800px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <el-tabs v-model="activeTab">
      <!-- 单条新增 -->
      <el-tab-pane label="单条新增" name="single">
        <el-form ref="singleFormRef" :model="singleForm" :rules="singleRules" label-width="120px">
          <el-form-item label="客户" prop="customer_id">
            <span class="customer-name">{{ order?.customer_name }}</span>
          </el-form-item>
          
          <el-form-item label="产品搜索" prop="search_keyword">
            <ProductSearchSelect
              v-model="selectedProduct"
              :customer-id="order?.customer_id"
              placeholder="搜索 OE号 / 客户型号 / 产品名称"
              @select="onProductSelect"
              @clear="onSearchClear"
            />
          </el-form-item>
          
          <template v-if="selectedProduct">
            <el-divider content-position="left">已选产品</el-divider>
            <div class="selected-product-info">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="OE号">{{ selectedProduct.oes?.[0] }}</el-descriptions-item>
                <el-descriptions-item label="产品名称">{{ selectedProduct.product_name }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
          
          <el-divider content-position="left">产品信息</el-divider>
          
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="客户产品编号" prop="customer_code">
                <el-input v-model="singleForm.customer_code" placeholder="客户产品编号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="OE号" prop="oe_number">
                <el-input v-model="singleForm.oe_number" placeholder="OE号" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="产品名称" prop="detail_desc">
                <el-input v-model="singleForm.detail_desc" placeholder="产品名称" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="数量" prop="quantity">
                <el-input-number v-model="singleForm.quantity" :min="1" :max="999999" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="单价(USD)" prop="unit_price">
                <el-input-number v-model="singleForm.unit_price" :min="0.01" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="合计金额">
                <div class="amount-display">$ {{ formatAmount(singleForm.quantity * singleForm.unit_price) }}</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
      
      <!-- Excel 导入 -->
      <el-tab-pane label="Excel 导入" name="excel">
        <div class="excel-import-area">
          <el-upload
            ref="uploadRef"
            class="excel-uploader"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽 Excel 文件到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx 和 .xls 格式，文件应包含产品信息列
              </div>
            </template>
          </el-upload>
          
          <template v-if="excelData.length > 0">
            <el-divider content-position="left">数据预览（前 10 行）</el-divider>
            
            <el-form :model="columnMapping" label-width="120px" inline>
              <el-form-item label="客户产品编号">
                <el-select v-model="columnMapping.customer_code" placeholder="选择列" style="width: 150px">
                  <el-option v-for="h in excelHeaders" :key="h" :label="h" :value="h" />
                </el-select>
              </el-form-item>
              <el-form-item label="OE号">
                <el-select v-model="columnMapping.oe_number" placeholder="选择列" style="width: 150px">
                  <el-option v-for="h in excelHeaders" :key="h" :label="h" :value="h" />
                </el-select>
              </el-form-item>
              <el-form-item label="产品名称">
                <el-select v-model="columnMapping.product_name" placeholder="选择列" style="width: 150px">
                  <el-option v-for="h in excelHeaders" :key="h" :label="h" :value="h" />
                </el-select>
              </el-form-item>
              <el-form-item label="数量">
                <el-select v-model="columnMapping.quantity" placeholder="选择列" style="width: 150px">
                  <el-option v-for="h in excelHeaders" :key="h" :label="h" :value="h" />
                </el-select>
              </el-form-item>
              <el-form-item label="单价">
                <el-select v-model="columnMapping.unit_price" placeholder="选择列" style="width: 150px">
                  <el-option v-for="h in excelHeaders" :key="h" :label="h" :value="h" />
                </el-select>
              </el-form-item>
            </el-form>
            
            <el-table :data="previewData" stripe size="small" max-height="300">
              <el-table-column v-for="h in excelHeaders.slice(0, 8)" :key="h" :prop="h" :label="h" min-width="120" show-overflow-tooltip />
            </el-table>
            
            <div class="import-summary">
              共 {{ excelData.length }} 条数据，待导入 {{ validDataCount }} 条
            </div>
          </template>
        </div>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="onClose">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">
          {{ activeTab === 'single' ? '添加产品' : '导入产品' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Search, UploadFilled } from '@element-plus/icons-vue'
import type { OrderListItem } from '@/types/orderSummary'
import * as XLSX from 'xlsx'
import { apiUrl } from '@/api/base'
import { ORDERS_BFF, PRODUCT_CUSTOMER } from '@/api/endpoints'
import ProductSearchSelect from '@/components/common/ProductSearchSelect.vue'
import type { CustomerProductSearchItem } from '@/api/customerProduct'

const visible = ref(false)
const submitting = ref(false)
const activeTab = ref('single')
const singleFormRef = ref<FormInstance>()
const uploadRef = ref()
const order = ref<OrderListItem | null>(null)

interface ProductSuggestion {
  id: number
  oe_number: string
  detail_desc: string
  product_code?: string
}

const selectedProduct = ref<CustomerProductSearchItem | null>(null)

const singleForm = reactive({
  search_keyword: '',
  customer_code: '',
  customer_model: '',
  oe_number: '',
  detail_desc: '',
  quantity: 1,
  unit_price: 0
})

const singleRules: FormRules = {
  customer_code: [{ required: true, message: '请输入客户产品编号', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

// Excel 导入相关
const excelData = ref<any[]>([])
const excelHeaders = ref<string[]>([])
const columnMapping = reactive<Record<string, string>>({
  customer_code: '',
  oe_number: '',
  product_name: '',
  quantity: '',
  unit_price: ''
})

const previewData = computed(() => excelData.value.slice(0, 10))

const validDataCount = computed(() => {
  return excelData.value.filter(row => {
    const code = row[columnMapping.customer_code]
    return code && String(code).trim()
  }).length
})

const emit = defineEmits<{
  (e: 'success'): void
}>()

function formatAmount(amount: number): string {
  return isNaN(amount) ? '0.00' : amount.toFixed(2)
}

// onProductSelect
function onProductSelect(item: CustomerProductSearchItem) {
  selectedProduct.value = item
  singleForm.customer_code = item.customer_code || item.customer_model || ''
  singleForm.customer_model = item.customer_model || ''
  singleForm.oe_number = item.oes[0] || ''
  singleForm.detail_desc = item.product_name || ''
  singleForm.unit_price = item.price_usd || 0
}

function onSearchClear() {
  selectedProduct.value = null
  singleForm.customer_code = ''
  singleForm.customer_model = ''
  singleForm.oe_number = ''
  singleForm.detail_desc = ''
  singleForm.unit_price = 0
}

// Excel 文件处理
function onFileChange(file: any) {
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
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
      
      if (jsonData.length > 0) {
        excelHeaders.value = (jsonData[0] as string[]).map(h => String(h || ''))
        excelData.value = jsonData.slice(1).map(row => {
          const obj: Record<string, any> = {}
          excelHeaders.value.forEach((h, i) => {
            obj[h] = (row as any[])[i]
          })
          return obj
        })
        
        // 自动匹配列名
        autoMatchColumns()
      }
    } catch (err) {
      ElMessage.error('读取 Excel 文件失败')
      excelData.value = []
      excelHeaders.value = []
    }
  }
  reader.readAsArrayBuffer(file.raw)
}

function onFileRemove() {
  excelData.value = []
  excelHeaders.value = []
}

function autoMatchColumns() {
  const mapping: Record<string, string[]> = {
    customer_code: ['客户产品编号', 'customer_code', '产品编号', '编号'],
    oe_number: ['OE号', 'oe_number', 'OE', 'oe'],
    product_name: ['产品名称', 'product_name', '名称', 'name'],
    quantity: ['数量', 'quantity', 'qty', '数量(EA)'],
    unit_price: ['单价', 'unit_price', '报价', 'price']
  }
  
  for (const [field, keywords] of Object.entries(mapping)) {
    for (const header of excelHeaders.value) {
      const h = header.toLowerCase()
      if (keywords.some(k => h.includes(k.toLowerCase()))) {
        columnMapping[field] = header
        break
      }
    }
  }
}

// 提交
async function onSubmit() {
  if (activeTab.value === 'single') {
    await submitSingle()
  } else {
    await submitExcel()
  }
}

async function submitSingle() {
  if (!singleFormRef.value) return
  
  await singleFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (!order.value?.id) return
    
    submitting.value = true
    try {
      const res = await fetch(apiUrl(ORDERS_BFF.supplementItems(order.value.id)), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: [{
            product_code: singleForm.customer_code,
            customer_code: singleForm.customer_code,
            customer_model: singleForm.customer_model || undefined,
            oe_number: singleForm.oe_number || undefined,
            detail_desc: singleForm.detail_desc || undefined,
            quantity: singleForm.quantity,
            unit_price: singleForm.unit_price
          }]
        })
      })
      
      if (res.ok) {
        ElMessage.success('产品添加成功')
        emit('success')
        onClose()
      } else {
        const err = await res.json()
        ElMessage.error(err.message || '添加失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '添加产品失败')
    } finally {
      submitting.value = false
    }
  })
}

async function submitExcel() {
  if (excelData.value.length === 0) {
    ElMessage.warning('请先上传 Excel 文件')
    return
  }
  
  if (!columnMapping.customer_code) {
    ElMessage.warning('请选择客户产品编号列')
    return
  }
  
  if (!order.value?.id) return
  
  submitting.value = true
  try {
    const items = excelData.value
      .filter(row => row[columnMapping.customer_code])
      .map(row => ({
        customer_code: String(row[columnMapping.customer_code] || '').trim(),
        oe_number: columnMapping.oe_number ? String(row[columnMapping.oe_number] || '').trim() : undefined,
        detail_desc: columnMapping.product_name ? String(row[columnMapping.product_name] || '').trim() : undefined,
        quantity: parseFloat(row[columnMapping.quantity]) || 1,
        unit_price: parseFloat(row[columnMapping.unit_price]) || 0
      }))
      .filter(item => item.customer_code)
    
    if (items.length === 0) {
      ElMessage.warning('没有找到有效的数据')
      return
    }
    
    const res = await fetch(apiUrl(ORDERS_BFF.supplementItems(order.value.id)), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items })
    })
    
    if (res.ok) {
      const data = await res.json()
      ElMessage.success(`成功导入 ${data.created_count || items.length} 项产品`)
      emit('success')
      onClose()
    } else {
      const err = await res.json()
      ElMessage.error(err.message || '导入失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '导入产品失败')
  } finally {
    submitting.value = false
  }
}

function onClose() {
  singleFormRef.value?.resetFields()
  singleForm.search_keyword = ''
  singleForm.customer_code = ''
  singleForm.customer_model = ''
  singleForm.oe_number = ''
  singleForm.detail_desc = ''
  singleForm.quantity = 1
  singleForm.unit_price = 0
  selectedProduct.value = null
  excelData.value = []
  excelHeaders.value = []
  Object.keys(columnMapping).forEach(k => columnMapping[k] = '')
  visible.value = false
}

function open(orderData: OrderListItem) {
  order.value = orderData
  visible.value = true
  activeTab.value = 'single'
}

defineExpose({ open })
</script>

<style scoped>
.customer-name {
  color: #409eff;
  font-weight: 500;
}

.amount-display {
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
}

.product-suggestion .oe-number {
  color: #909399;
  font-size: 12px;
  min-width: 100px;
}

.product-suggestion .product-name {
  flex: 1;
}

.excel-import-area {
  padding: 10px 0;
}

.excel-uploader {
  text-align: center;
}

.import-summary {
  margin-top: 16px;
  text-align: center;
  color: #909399;
}
</style>
