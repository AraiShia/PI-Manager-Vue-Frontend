<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="90vw"
    top="5vh"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <div v-if="item" class="product-edit-dialog">
      <!-- 基础信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #fde2e2; color: #c45650;">基础信息</div>
        <div class="section-body">
          <div class="form-grid">
            <!-- 第一行：客户、国家、客户型号 -->
            <div class="form-item">
              <label class="required">客户</label>
              <el-input v-model="form.customer_name" disabled />
            </div>
            <div class="form-item">
              <label>国家</label>
              <el-input v-model="form.customer_country" disabled />
            </div>
            <div class="form-item">
              <label class="required">客户型号</label>
              <FieldInput
                v-model="form.customer_model"
                :status="getFieldStatus('customer_model')"
                @blur="saveField('customer_model', form.customer_model)"
              />
            </div>
            <div class="form-item"></div>

            <!-- 第二行：主图、附图 -->
            <div class="form-item wide image-item">
              <label>主图</label>
              <el-upload
                class="image-uploader"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
              >
                <img v-if="form.image_url" :src="form.image_url" class="preview-image" alt="主图" />
                <el-button v-else type="primary" size="small" plain>上传主图</el-button>
              </el-upload>
            </div>
            <div class="form-item wide image-item">
              <label>附图</label>
              <el-upload
                class="image-uploader"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImage2Change"
              >
                <img v-if="form.image_url_2" :src="form.image_url_2" class="preview-image" alt="附图" />
                <el-button v-else type="primary" size="small" plain>上传附图</el-button>
              </el-upload>
            </div>

            <!-- 第三行：产品名称中文、英文、产品颜色 -->
            <div class="form-item">
              <label class="required">产品名称（中文）</label>
              <FieldInput
                v-model="form.product_name"
                :status="getFieldStatus('detail_desc')"
                @blur="saveField('detail_desc', form.product_name)"
              />
            </div>
            <div class="form-item">
              <label>产品名称（英文）</label>
              <FieldInput
                v-model="form.product_name_en"
                :status="getFieldStatus('detail_desc_en')"
                @blur="saveField('detail_desc_en', form.product_name_en)"
              />
            </div>
            <div class="form-item">
              <label>产品颜色</label>
              <FieldInput
                v-model="form.product_feature"
                :status="getFieldStatus('product_feature')"
                @blur="saveField('product_feature', form.product_feature)"
              />
            </div>
            <div class="form-item"></div>

            <!-- 第四行：OE号、编号备注（高框） -->
            <div class="form-item tall">
              <label>OE号（索引）</label>
              <el-input
                v-model="form.oe_number"
                type="textarea"
                :rows="3"
                resize="none"
                @blur="saveField('oe_number', form.oe_number)"
              />
            </div>
            <div class="form-item tall">
              <label>编号备注</label>
              <el-input
                v-model="form.remark"
                type="textarea"
                :rows="3"
                resize="none"
                @blur="saveField('remark', form.remark)"
              />
            </div>
            <div class="form-item"></div>
            <div class="form-item"></div>
          </div>
        </div>
      </div>

      <!-- 销售细节 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #fef0f0; color: #b88230;">销售细节</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="form-item">
              <label>预估毛利率</label>
              <el-input :model-value="estimatedMarginRate" readonly />
            </div>
            <div class="form-item">
              <label>价格变动</label>
              <FieldInput
                v-model="form.price_change"
                :status="getFieldStatus('price_change')"
                @blur="onUnmappedBlur('price_change')"
              />
            </div>
            <div class="form-item"></div>
            <div class="form-item">
              <label class="required">采购数量</label>
              <el-input-number
                v-model="form.quantity"
                :min="0"
                style="width: 100%"
                @blur="saveField('quantity', form.quantity)"
              />
            </div>
            <div class="form-item">
              <label class="required">报价 USD</label>
              <el-input-number
                v-model="form.unit_price"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('unit_price', form.unit_price)"
              />
            </div>
            <div class="form-item">
              <label>金额</label>
              <el-input :model-value="formatMoney(computedAmount)" readonly />
            </div>
            <div class="form-item">
              <label>客户需求</label>
              <FieldInput
                v-model="form.customer_demand"
                :status="getFieldStatus('customer_demand')"
                @blur="onUnmappedBlur('customer_demand')"
              />
            </div>
            <div class="form-item">
              <label>答复</label>
              <FieldInput
                v-model="form.reply"
                :status="getFieldStatus('reply')"
                @blur="onUnmappedBlur('reply')"
              />
            </div>
            <div class="form-item">
              <label>确定信息</label>
              <FieldInput
                v-model="form.confirm_info"
                :status="getFieldStatus('confirm_info')"
                @blur="onUnmappedBlur('confirm_info')"
              />
            </div>
            <div class="form-item">
              <label>报价备注</label>
              <FieldInput
                v-model="form.quote_remark"
                :status="getFieldStatus('quote_remark')"
                @blur="onUnmappedBlur('quote_remark')"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 采购信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #e1f3d8; color: #5daf34;">采购信息</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="form-item">
              <label>预估美金价</label>
              <el-input-number
                v-model="form.estimated_usd_price"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('estimated_usd_price', form.estimated_usd_price)"
              />
            </div>
            <div class="form-item">
              <label class="required">人民币采购价</label>
              <el-input-number
                v-model="form.purchase_price"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('purchase_price', form.purchase_price)"
              />
            </div>
            <div class="form-item">
              <label>贴标费</label>
              <el-input-number
                v-model="form.misc_fee"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('misc_fee', form.misc_fee)"
              />
            </div>
            <div class="form-item">
              <label>运费</label>
              <el-input-number
                v-model="form.shipping_fee"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('shipping_fee', form.shipping_fee)"
              />
            </div>
            <div class="form-item">
              <label>金额</label>
              <el-input :model-value="formatMoney(purchaseAmount)" readonly />
            </div>
            <div class="form-item">
              <label>开票情况</label>
              <FieldInput
                v-model="form.invoice_status"
                :status="getFieldStatus('invoice_status')"
                @blur="saveField('invoice_status', form.invoice_status)"
              />
            </div>
            <div class="form-item">
              <label class="required">供应商</label>
              <FieldInput
                v-model="form.factory_name"
                :status="getFieldStatus('factory_name')"
                @blur="saveField('factory_name', form.factory_name)"
              />
            </div>
            <div class="form-item wide">
              <label>供应商链接</label>
              <FieldInput
                v-model="form.shop_url"
                :status="getFieldStatus('shop_url')"
                @blur="saveField('shop_url', form.shop_url)"
              />
            </div>
            <div class="form-item all">
              <label>产品特性/选项/采购备注</label>
              <el-input
                v-model="form.product_detail"
                type="textarea"
                :rows="2"
                @blur="saveField('product_detail', form.product_detail)"
              />
            </div>
            <div class="form-item">
              <label>采购方式</label>
              <FieldInput
                v-model="form.purchase_option_name"
                :status="getFieldStatus('purchase_option_name')"
                @blur="saveField('purchase_option_name', form.purchase_option_name)"
              />
            </div>
            <div class="form-item">
              <label>付款方式</label>
              <FieldInput
                v-model="form.payment_method"
                :status="getFieldStatus('payment_method')"
                @blur="onUnmappedBlur('payment_method')"
              />
            </div>
            <div class="form-item">
              <label>付款1</label>
              <el-input-number
                v-model="form.factory_deposit"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('factory_deposit', form.factory_deposit)"
              />
            </div>
            <div class="form-item">
              <label>付款2</label>
              <el-input-number
                v-model="form.factory_balance"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('factory_balance', form.factory_balance)"
              />
            </div>
            <div class="form-item">
              <label>未付款金额</label>
              <el-input :model-value="formatMoney(unpaidAmount)" readonly />
            </div>
            <div class="form-item wide">
              <label>开票工厂（全称）</label>
              <FieldInput
                v-model="form.factory_invoice_name"
                :status="getFieldStatus('factory_invoice_name')"
                @blur="onUnmappedBlur('factory_invoice_name')"
              />
            </div>
            <div class="form-item">
              <label>货源地</label>
              <FieldInput
                v-model="form.source_place"
                :status="getFieldStatus('source_place')"
                @blur="onUnmappedBlur('source_place')"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 收货入库信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #d9ecff; color: #409eff;">收货入库信息</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="form-item">
              <label>入库数量</label>
              <el-input-number
                v-model="form.stock_in_quantity"
                :min="0"
                style="width: 100%"
                @blur="saveField('stocked_qty', form.stock_in_quantity)"
              />
            </div>
            <div class="form-item">
              <label>箱数</label>
              <el-input-number
                v-model="form.carton_count"
                :min="0"
                style="width: 100%"
                @blur="saveField('carton_count', form.carton_count)"
              />
            </div>
            <div class="form-item">
              <label>总重量</label>
              <el-input-number
                v-model="form.total_weight"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('total_weight', form.total_weight)"
              />
            </div>
            <div class="form-item">
              <label>入库日期</label>
              <el-date-picker
                v-model="form.delivery_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择日期"
                style="width: 100%"
                @change="saveField('delivery_date', form.delivery_date)"
              />
            </div>
            <div class="form-item all">
              <label>纸箱规格</label>
              <el-input
                v-model="form.carton_size"
                @blur="saveField('carton_size', form.carton_size)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 采购资料存档 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #f2f6fc; color: #606266;">采购资料存档</div>
        <div class="section-body">
          <div class="form-grid">
            <div v-for="archiveSlot in archiveSlots" :key="archiveSlot.key" class="form-item">
              <label>{{ archiveSlot.label }}</label>
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="createArchiveHandler(archiveSlot.key)"
              >
                <el-button type="primary" size="small" plain>
                  {{ archiveFileNames[archiveSlot.key] ? '重新选择' : '选择文件' }}
                </el-button>
              </el-upload>
              <div v-if="archiveFileNames[archiveSlot.key]" class="archive-file-name">
                {{ archiveFileNames[archiveSlot.key] }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="close">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useProductEdit, type FieldStatus } from '@/composables/useProductEdit'
import { orderSummaryApi } from '@/api/orderSummary'
import type { OrderDetailItem } from '@/types/orderSummary'
import FieldInput from './FieldInput.vue'

interface ProductEditItem extends OrderDetailItem {
  customer_name?: string
  customer_country?: string
}

interface ProductEditForm {
  customer_name: string
  customer_country: string
  customer_model: string
  image_url: string
  image_url_2: string
  product_name: string
  product_name_en: string
  product_feature: string
  oe_number: string
  remark: string
  quantity: number
  unit_price: number
  estimated_margin: number | undefined
  price_change: string
  customer_demand: string
  reply: string
  confirm_info: string
  quote_remark: string
  estimated_usd_price: number | undefined
  purchase_price: number
  misc_fee: number
  shipping_fee: number
  invoice_status: string
  factory_name: string
  shop_url: string
  product_detail: string
  purchase_option_name: string
  payment_method: string
  factory_deposit: number | undefined
  factory_balance: number | undefined
  factory_invoice_name: string
  source_place: string
  stock_in_quantity: number
  carton_count: number | undefined
  total_weight: number | undefined
  delivery_date: string
  carton_size: string
}

const visible = ref(false)
const item = ref<ProductEditItem | null>(null)
const { fieldStates, saveField } = useProductEdit(item as any)

const form = reactive<ProductEditForm>({
  customer_name: '',
  customer_country: '',
  customer_model: '',
  image_url: '',
  image_url_2: '',
  product_name: '',
  product_name_en: '',
  product_feature: '',
  oe_number: '',
  remark: '',
  quantity: 0,
  unit_price: 0,
  estimated_margin: undefined,
  price_change: '',
  customer_demand: '',
  reply: '',
  confirm_info: '',
  quote_remark: '',
  estimated_usd_price: undefined,
  purchase_price: 0,
  misc_fee: 0,
  shipping_fee: 0,
  invoice_status: '',
  factory_name: '',
  shop_url: '',
  product_detail: '',
  purchase_option_name: '',
  payment_method: '',
  factory_deposit: undefined,
  factory_balance: undefined,
  factory_invoice_name: '',
  source_place: '',
  stock_in_quantity: 0,
  carton_count: undefined,
  total_weight: undefined,
  delivery_date: '',
  carton_size: '',
})

const archiveFileNames = reactive<Record<string, string>>({
  contract: '',
  invoice: '',
  payment: '',
  waybill: '',
})

const archiveSlots = [
  { key: 'contract', label: '合同' },
  { key: 'invoice', label: '发票' },
  { key: 'payment', label: '付款凭证' },
  { key: 'waybill', label: '运单凭证' },
]

const dialogTitle = computed(() => {
  const name = item.value?.customer_model || item.value?.product_code || ''
  return `编辑产品 - ${name}`
})

const computedAmount = computed(() => {
  const qty = Number(form.quantity || 0)
  const price = Number(form.unit_price || 0)
  return qty * price
})

const purchaseAmount = computed(() => {
  const price = Number(form.purchase_price || 0)
  const qty = Number(form.quantity || 0)
  const misc = Number(form.misc_fee || 0)
  const shipping = Number(form.shipping_fee || 0)
  return price * qty + misc + shipping
})

const unpaidAmount = computed(() => {
  const total = purchaseAmount.value
  const deposit = Number(form.factory_deposit || 0)
  const balance = Number(form.factory_balance || 0)
  return total - deposit - balance
})

const estimatedMarginRate = computed(() => {
  const revenue = computedAmount.value
  const cost = purchaseAmount.value
  if (!revenue) return ''
  const rate = ((revenue - cost) / revenue) * 100
  return `${rate.toFixed(2)}%`
})

const emit = defineEmits<{
  (e: 'closed'): void
}>()

function getFieldStatus(field: string): FieldStatus {
  return fieldStates.value[field]?.status || 'idle'
}

function initFromItem(source: ProductEditItem) {
  form.customer_name = source.customer_name || ''
  form.customer_country = source.customer_country || ''
  form.customer_model = source.customer_model || ''
  form.image_url = source.image_url || ''
  form.image_url_2 = source.image_url_2 || ''
  form.product_name = source.product_name || ''
  form.product_name_en = source.product_name_en || ''
  form.product_feature = source.product_feature || ''
  form.oe_number = source.oe_number || ''
  form.remark = source.remark || ''
  form.quantity = source.quantity || 0
  form.unit_price = source.unit_price || 0
  form.estimated_margin = source.estimated_margin ?? undefined
  form.estimated_usd_price = source.estimated_usd_price ?? undefined
  form.purchase_price = source.purchase_price || 0
  form.misc_fee = source.misc_fee || 0
  form.shipping_fee = source.shipping_fee || 0
  form.invoice_status = source.invoice_status || ''
  form.factory_name = source.factory_name || ''
  form.shop_url = source.shop_url || ''
  form.product_detail = source.product_detail || ''
  form.purchase_option_name = source.purchase_option_name || ''
  form.factory_deposit = source.factory_deposit ?? undefined
  form.factory_balance = source.factory_balance ?? undefined
  form.stock_in_quantity = source.stock_in_quantity || 0
  form.carton_count = source.carton_count ?? undefined
  form.total_weight = source.total_weight ?? undefined
  form.delivery_date = source.delivery_date || ''
  form.carton_size = source.carton_size || ''
}

function open(source: OrderDetailItem, customerName?: string, customerCountry?: string) {
  const editItem: ProductEditItem = {
    ...source,
    customer_name: customerName || '',
    customer_country: customerCountry || '',
  }
  item.value = editItem
  initFromItem(editItem)
  visible.value = true
}

function close() {
  visible.value = false
}

function onClosed() {
  emit('closed')
}

function onUnmappedBlur(field: string) {
  // 这些字段没有对应的后端列，仅做 UI 展示
  console.debug(`Field ${field} has no backend mapping, skipping save`)
}

function formatMoney(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || amount === '') return ''
  const n = Number(amount)
  return isNaN(n) ? '' : n.toFixed(2)
}

async function handleImageChange(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.image_url = res.data.data.url
      await saveField('image_url', form.image_url)
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

async function handleImage2Change(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.image_url_2 = res.data.data.url
      await saveField('image_url_2', form.image_url_2)
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

function createArchiveHandler(key: string) {
  return (file: any) => handleArchiveChange(key, file)
}

async function handleArchiveChange(key: string, file: any) {
  archiveFileNames[key] = file.name || ''
  ElMessage.info(`${key} 已选择: ${file.name}`)
}

defineExpose({ open, close })
</script>

<style scoped>
.product-edit-dialog {
  max-height: 75vh;
  overflow-y: auto;
  padding-right: 8px;
}

.edit-section {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 16px;
  overflow: hidden;
}

.section-title {
  padding: 10px 16px;
  font-weight: 600;
  font-size: 14px;
}

.section-body {
  padding: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-item.wide {
  grid-column: span 2;
}

.form-item.all {
  grid-column: span 4;
}

.form-item.tall {
  grid-row: span 2;
}

.form-item.tall :deep(.el-textarea__inner) {
  flex: 1;
  height: 100%;
  min-height: 72px;
}

.form-item.image-item :deep(.el-upload) {
  display: block;
  height: 120px;
}

.form-item label {
  font-size: 12px;
  color: #606266;
}

.form-item label.required::before {
  content: '* ';
  color: #f56c6c;
}

.image-uploader {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  cursor: pointer;
  overflow: hidden;
}

.image-uploader:hover {
  border-color: #409eff;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.archive-file-name {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}
</style>
