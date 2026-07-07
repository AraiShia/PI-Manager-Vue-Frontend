<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="95vw"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <div v-if="item" class="product-edit-dialog">
      <!-- 基础信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #fde2e2; color: #c45650;">基础信息</div>
        <div class="section-body">
          <!-- 第一行：客户、客户型号、国家 -->
          <div class="form-grid info-row-3">
            <div class="form-item">
              <label class="required">客户</label>
              <el-input v-model="form.customer_name" disabled />
            </div>
            <div class="form-item">
              <label class="required">客户型号</label>
              <FieldInput
                v-model="form.customer_model"
                :status="getFieldStatus('customer_model')"
                @blur="saveField('customer_model', form.customer_model)"
              />
            </div>
            <div class="form-item">
              <label>国家</label>
              <el-input v-model="form.customer_country" disabled />
            </div>
          </div>

          <!-- 第二行：主图、附图、中文名、英文名（同一行紧凑布局） -->
          <div class="compact-image-name-row">
            <div class="image-cell main-image-block">
              <label>主图</label>
              <el-upload
                class="image-uploader-main"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
              >
                <img v-if="form.image_url" :src="form.image_url" class="preview-image-main" alt="主图" />
                <el-icon v-else class="image-placeholder-icon"><Plus /></el-icon>
              </el-upload>
            </div>
            <div class="image-cell extra-image-block">
              <label>附图 ({{ form.extra_images.length }})</label>
              <div class="extra-images-scroll">
                <div
                  v-for="(img, idx) in form.extra_images"
                  :key="idx"
                  class="extra-image-item"
                >
                  <img :src="img" alt="附图" />
                  <el-icon class="remove-icon" @click="removeExtraImage(idx)"><Close /></el-icon>
                </div>
                <el-upload
                  class="extra-image-uploader"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleExtraImageChange"
                >
                  <el-icon class="image-placeholder-icon"><Plus /></el-icon>
                </el-upload>
              </div>
            </div>
            <!-- 产品名称（中英文两行输入，表格布局） -->
            <div class="name-table-row">
              <div class="name-label">
                <span class="required">*</span>
                <div>产品名称</div>
              </div>
              <div class="name-row-zh">
                <div class="name-input-label">中文名</div>
                <div class="name-input-cell">
                  <el-input
                    v-model="form.product_name"
                    @blur="saveField('detail_desc', form.product_name)"
                  />
                </div>
              </div>
              <div class="name-row-en">
                <div class="name-input-label">英文名</div>
                <div class="name-input-cell">
                  <FieldInput
                    v-model="form.product_name_en"
                    :status="getFieldStatus('detail_desc_en')"
                    @blur="saveField('detail_desc_en', form.product_name_en)"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 第三行：产品颜色 -->
          <div class="form-grid info-row-4">
            <div class="form-item">
              <label>产品需求</label>
              <FieldInput
                v-model="form.product_acquires"
                :status="getFieldStatus('product_acquires')"
                @blur="saveField('product_acquires', form.product_acquires)"
              />
            </div>
            <div class="form-item">
              <label>产品颜色</label>
              <FieldInput
                v-model="form.product_color"
                :status="getFieldStatus('product_color')"
                @blur="saveField('product_color', form.product_color)"
              />
            </div>
            <div class="form-item">
              <label>产品类别</label>
              <el-input :model-value="productCategoryDisplay" readonly />
            </div>
            <div class="form-item"></div>
            <div class="form-item"></div>
          </div>

          <!-- 第四行：OE号、编号备注（高框） -->
          <div class="form-grid info-row-4">
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
                @blur="onRemarkBlur"
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
          <div class="sales-detail-table">
            <!-- 第1行：综合毛利额 + 预估毛利率 + 价格变动 -->
            <div class="sales-summary-head">综合毛利额:</div>
            <div class="sales-summary-cell span-2">{{ formatMoney(estimatedProfit) }}</div>
            <div class="sales-summary-head">预估毛利率:</div>
            <div class="sales-summary-cell">{{ estimatedMarginRate }}</div>
            <div class="sales-summary-head">价格变动:</div>
            <div class="sales-summary-cell">
              <FieldInput
                v-model="form.price_change"
                :status="getFieldStatus('price_change')"
                @blur="onUnmappedBlur('price_change')"
              />
            </div>

            <!-- 第2行：字段标题 -->
            <div class="sales-detail-head required">采购数量<br />QTY</div>
            <div class="sales-detail-head required">报价<br />PRICE/USD</div>
            <div class="sales-detail-head">金额<br />TOTAL</div>
            <div class="sales-detail-head">客户需求<br />Comments</div>
            <div class="sales-detail-head">答复<br />reply</div>
            <div class="sales-detail-head">确定信息<br />confirmation</div>
            <div class="sales-detail-head">报价备注<br />Q.Notes</div>

            <!-- 第3行：字段值 -->
            <div class="sales-detail-cell">
              <el-input-number
                v-model="form.quantity"
                :min="0"
                style="width: 100%"
                @blur="saveField('quantity', form.quantity)"
              />
            </div>
            <div class="sales-detail-cell">
              <el-input-number
                v-model="form.unit_price"
                :min="0"
                :precision="2"
                style="width: 100%"
                @blur="saveField('unit_price', form.unit_price)"
              />
            </div>
            <div class="sales-detail-cell amount-cell">{{ formatMoney(computedAmount) }}</div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.customer_demand"
                :status="getFieldStatus('customer_demand')"
                @blur="onUnmappedBlur('customer_demand')"
              />
            </div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.reply"
                :status="getFieldStatus('reply')"
                @blur="onUnmappedBlur('reply')"
              />
            </div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.confirm_info"
                :status="getFieldStatus('confirm_info')"
                @blur="onUnmappedBlur('confirm_info')"
              />
            </div>
            <div class="sales-detail-cell">
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
          <div class="purchase-cost-table">
              <!-- 第1行：价格 + 开票情况（沿用原表头） -->
              <div class="purchase-cost-head">预估美金价</div>
              <div class="purchase-cost-head required">人民币采购价</div>
              <div class="purchase-cost-head">贴标费</div>
              <div class="purchase-cost-head">运费</div>
              <div class="purchase-cost-head">金额</div>
              <div class="purchase-cost-head invoice-group-head">开票情况</div>

              <div class="purchase-cost-cell">
                <el-input-number
                  v-model="form.estimated_usd_price"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('estimated_usd_price', form.estimated_usd_price)"
                />
              </div>
              <div class="purchase-cost-cell">
                <el-input-number
                  v-model="form.purchase_price"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('purchase_price', form.purchase_price)"
                />
              </div>
              <div class="purchase-cost-cell">
                <el-input-number
                  v-model="form.misc_fee"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('misc_fee', form.misc_fee)"
                />
              </div>
              <div class="purchase-cost-cell">
                <el-input-number
                  v-model="form.shipping_fee"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('shipping_fee', form.shipping_fee)"
                />
              </div>
              <div class="purchase-cost-cell amount-cell">
                {{ formatMoney(form.purchase_price * form.quantity + (form.misc_fee || 0) + (form.shipping_fee || 0)) }}
              </div>
              <div class="purchase-cost-cell invoice-type-cell">
                <el-select
                  v-model="form.invoice_type"
                  placeholder="类型"
                  size="small"
                  style="width: 100%"
                  @change="saveField('invoice_type', form.invoice_type)"
                >
                  <el-option label="增票" value="增票" />
                  <el-option label="普票" value="普票" />
                  <el-option label="不开票" value="不开票" />
                </el-select>
              </div>
              <div class="purchase-cost-cell invoice-rate-cell">
                <el-input
                  v-model="form.invoice_rate"
                  size="small"
                  placeholder="备注"
                  @blur="saveField('invoice_rate', form.invoice_rate)"
                />
              </div>

              <!-- 第3行：供应商 + 产品特性标题 -->
              <div class="purchase-cost-head span-2 required">供应商（HJLK2204）</div>
              <div class="purchase-cost-cell span-2">
                <FieldInput
                  v-model="form.factory_name"
                  :status="getFieldStatus('factory_name')"
                  @blur="saveField('factory_name', form.factory_name)"
                />
              </div>
              <div class="purchase-cost-head required">产品特性/选项/采购备注</div>
              <div class="purchase-cost-cell span-2 product-detail-cell detail-right" rowspan="2">
                <el-input
                  v-model="form.product_detail"
                  type="textarea"
                  :rows="3"
                  resize="none"
                  @blur="saveField('product_detail', form.product_detail)"
                />
              </div>

              <!-- 第4行：供应商链接 + 产品特性内容 -->
              <div class="purchase-cost-head span-2">供应商链接</div>
              <div class="purchase-cost-cell span-2 link-cell">
                <FieldInput
                  v-model="form.shop_url"
                  :status="getFieldStatus('shop_url')"
                  @blur="saveField('shop_url', form.shop_url)"
                />
              </div>
              <div class="purchase-cost-head detail-label-placeholder"></div>

              <!-- 第5行：采购方式 + 付款标题 -->
              <div class="purchase-cost-head span-2">采购方式</div>
              <div class="purchase-cost-cell span-2">
                <FieldInput
                  v-model="form.purchase_option_name"
                  :status="getFieldStatus('purchase_option_name')"
                  @blur="saveField('purchase_option_name', form.purchase_option_name)"
                />
              </div>
              <div class="purchase-cost-head payment-head">付款1</div>
              <div class="purchase-cost-head payment-head">付款2</div>
              <div class="purchase-cost-head payment-head">未付款金额</div>

              <!-- 第6行：付款方式 + 付款金额 -->
              <div class="purchase-cost-head span-2">付款方式</div>
              <div class="purchase-cost-cell span-2">
                <FieldInput
                  v-model="form.payment_method"
                  :status="getFieldStatus('payment_method')"
                  @blur="saveField('payment_method', form.payment_method)"
                />
              </div>
              <div class="purchase-cost-cell payment-cell">
                <el-input-number
                  v-model="form.factory_deposit"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('factory_deposit', form.factory_deposit)"
                />
              </div>
              <div class="purchase-cost-cell payment-cell">
                <el-input-number
                  v-model="form.factory_balance"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @blur="saveField('factory_balance', form.factory_balance)"
                />
              </div>
              <div class="purchase-cost-cell amount-cell payment-cell">
                {{ formatMoney(unpaidAmount) }}
              </div>

              <!-- 第7行：开票工厂 + 货源地 -->
              <div class="purchase-cost-head span-2">开票工厂（全称）：</div>
              <div class="purchase-cost-cell span-2">
                <FieldInput
                  v-model="form.factory_invoice_name"
                  :status="getFieldStatus('factory_invoice_name')"
                  @blur="onUnmappedBlur('factory_invoice_name')"
                />
              </div>
              <div class="purchase-cost-head">货源地</div>
              <div class="purchase-cost-cell span-2">
                <FieldInput
                  v-model="form.source_place"
                  :status="getFieldStatus('source_place')"
                  @blur="onUnmappedBlur('source_place')"
                />
              </div>
            </div>
        </div>
      </div>

      <!-- 包装规格 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #f0f0f0; color: #666;">包装规格</div>
        <div class="section-body" style="padding: 8px 10px;">
          <table class="packaging-table">
            <thead>
              <tr>
                <th class="th-left">纸箱包装</th>
                <th colspan="3">长 × 宽 × 高 (cm)</th>
                <th>打包规格</th>
                <th>整箱毛重</th>
                <th>预估体积</th>
                <th>预估毛重</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="td-label">
                  <el-select v-model="form.packaging" style="width: 100%" @change="onPackagingChangeSave">
                    <el-option label="1件/箱" value="1件/箱" />
                    <el-option label="多件/箱" value="多件/箱" />
                    <el-option label="1件多箱" value="1件多箱" />
                  </el-select>
                </td>
                <td>
                  <el-input-number v-model="form.carton_length" :min="0" :precision="1" controls-position="right" style="width: 100%" @change="onCartonSizeChange" />
                </td>
                <td>
                  <el-input-number v-model="form.carton_width" :min="0" :precision="1" controls-position="right" style="width: 100%" @change="onCartonSizeChange" />
                </td>
                <td>
                  <el-input-number v-model="form.carton_height" :min="0" :precision="1" controls-position="right" style="width: 100%" @change="onCartonSizeChange" />
                </td>
                <td>
                  <div class="pack-spec-cell">
                    <el-input-number
                      v-if="form.packaging === '多件/箱'"
                      v-model="form.units_per_carton"
                      :min="1"
                      controls-position="right"
                      style="width: 100%"
                      @change="onUnitsPerCartonChange"
                    />
                    <el-input-number
                      v-else-if="form.packaging === '1件多箱'"
                      v-model="form.cartons_per_unit"
                      :min="1"
                      controls-position="right"
                      style="width: 100%"
                      @change="onCartonsPerUnitChange"
                    />
                    <el-input v-else :model-value="1" readonly style="width: 100%" />
                  </div>
                </td>
                <td>
                  <el-input-number v-model="form.carton_gross_weight" :min="0" :precision="2" controls-position="right" style="width: 100%" @change="saveField('carton_gross_weight', form.carton_gross_weight)" />
                </td>
                <td>
                  <el-input :model-value="form.estimated_volume != null ? form.estimated_volume.toFixed(6) : ''" readonly />
                </td>
                <td>
                  <el-input :model-value="estimatedGrossWeight" readonly />
                </td>
              </tr>
              <tr class="row-secondary">
                <td class="td-label">
                  <span class="row-secondary-label">数量 / 箱数</span>
                </td>
                <td colspan="4" class="row-secondary-text">
                  数量:
                  <el-input-number
                    v-model="form.quantity"
                    :min="0"
                    controls-position="right"
                    style="width: 110px; margin: 0 6px;"
                    @blur="saveField('quantity', form.quantity)"
                  />
                  箱数:
                  <el-input-number
                    v-model="form.carton_count"
                    :min="0"
                    controls-position="right"
                    style="width: 110px; margin: 0 6px;"
                    @blur="saveField('carton_count', form.carton_count)"
                  />
                  (自动:
                  <el-input :model-value="computedCartonCount" readonly style="width: 80px; display: inline-block; margin: 0 4px;" />
                  )
                </td>
                <td colspan="3">
                  纸箱尺寸:
                  <el-input
                    v-model="form.carton_size"
                    placeholder="如: 60x40x30"
                    style="width: calc(100% - 70px); display: inline-block; margin-left: 4px;"
                    @blur="onCartonSizeTextChange"
                  />
                </td>
              </tr>
            </tbody>
          </table>
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
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close } from '@element-plus/icons-vue'
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
  extra_images: string[]
  product_name: string
  product_name_en: string
  product_feature: string
  product_acquires: string
  product_color: string
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
  purchase_currency: 'RMB' | 'USD'
  exchange_rate: number
  profit_margin: number
  misc_fee: number
  shipping_fee: number
  invoice_status: string
  invoice_type: string
  invoice_rate: string
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
  // 包装规格相关字段
  packaging: '1件/箱' | '多件/箱' | '1件多箱'
  units_per_carton: number | undefined
  cartons_per_unit: number | undefined
  pack_spec: string
  estimated_volume: number | undefined
  carton_length: number | undefined
  carton_width: number | undefined
  carton_height: number | undefined
  carton_gross_weight: number | undefined
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
  extra_images: [] as string[],
  product_name: '',
  product_name_en: '',
  product_feature: '',
  product_acquires: '',
  product_color: '',
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
  purchase_currency: 'RMB',
  exchange_rate: 6.8,
  profit_margin: 25,
  misc_fee: 0,
  shipping_fee: 0,
  invoice_status: '',
  invoice_type: '',
  invoice_rate: '',
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
  // 包装规格相关字段
  packaging: '1件/箱',
  units_per_carton: undefined,
  cartons_per_unit: undefined,
  pack_spec: '',
  estimated_volume: undefined,
  carton_length: undefined,
  carton_width: undefined,
  carton_height: undefined,
  carton_gross_weight: undefined,
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

const productCategoryDisplay = computed(() => {
  const parentName = item.value?.category_parent_name
  const categoryName = item.value?.category_name
  if (parentName && categoryName) return `${parentName} / ${categoryName}`
  return parentName || categoryName || '-'
})

const computedAmount = computed(() => {
  const qty = Number(form.quantity || 0)
  const price = Number(form.unit_price || 0)
  return qty * price
})

const purchaseAmount = computed(() => {
  // 采购价 × 数量 + 贴标费 + 运费
  // 采购币种为人民币时，需要除以汇率折算成 USD（与客户报价币种对齐）
  const price = Number(form.purchase_price || 0)
  const qty = Number(form.quantity || 0)
  const misc = Number(form.misc_fee || 0)
  const shipping = Number(form.shipping_fee || 0)
  const rate = Number(form.exchange_rate || 6.8)
  const subtotal = (price * qty + misc + shipping)
  if (form.purchase_currency === 'RMB' && rate > 0) {
    return subtotal / rate
  }
  return subtotal
})

const unpaidAmount = computed(() => {
  const total = purchaseAmount.value
  const deposit = Number(form.factory_deposit || 0)
  const balance = Number(form.factory_balance || 0)
  return total - deposit - balance
})
const estimatedProfit = computed(() => {
  // 综合毛利额 = 美金金额(报价金额) × 汇率 − 采购金额
  const revenue = computedAmount.value
  const rate = Number(form.exchange_rate || 6.8)
  const profit = revenue * rate - purchaseAmount.value
  return Number.isFinite(profit) ? profit : 0
})

const estimatedMarginRate = computed(() => {
  const revenue = computedAmount.value
  const cost = purchaseAmount.value
  if (!revenue) return ''
  const rate = ((revenue - cost) / revenue) * 100
  return `${rate.toFixed(2)}%`
})

// 解析纸箱尺寸字符串为长宽高
function parseCartonSize(sizeStr: string): { l: number; w: number; h: number } {
  const parts = (sizeStr || '').split(/[xX×]/).map(s => parseFloat(s.trim()))
  return {
    l: parts[0] || 0,
    w: parts[1] || 0,
    h: parts[2] || 0,
  }
}

// 根据包装方式计算总箱数
const computedCartonCount = computed(() => {
  const qty = Number(form.quantity || 0)
  if (!qty) return 0
  if (form.packaging === '多件/箱') {
    const upc = Number(form.units_per_carton || 0)
    return upc > 0 ? Math.ceil(qty / upc) : 0
  } else if (form.packaging === '1件多箱') {
    const cpu = Number(form.cartons_per_unit || 0)
    return cpu > 0 ? cpu * qty : 0
  }
  return qty // 1件/箱
})

// 预估毛重 = 总箱数 × 整箱毛重
const estimatedGrossWeight = computed(() => {
  const cnt = Number(computedCartonCount.value || 0)
  const gw = Number(form.carton_gross_weight || 0)
  if (!cnt || !gw) return ''
  return (cnt * gw).toFixed(2)
})

// 包装方式切换
function onPackagingChange() {
  form.units_per_carton = undefined
  form.cartons_per_unit = undefined
  updatePackSpec()
}

// 包装方式切换（带保存）
function onPackagingChangeSave() {
  onPackagingChange()
  syncCartonCount()
  saveField('packaging', form.packaging)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 每箱件数变化（带保存）
function onUnitsPerCartonChange() {
  updatePackSpec()
  syncCartonCount()
  saveField('units_per_carton', form.units_per_carton)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 每件箱数变化（带保存）
function onCartonsPerUnitChange() {
  updatePackSpec()
  syncCartonCount()
  saveField('cartons_per_unit', form.cartons_per_unit)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 纸箱尺寸变化（带保存长宽高）
function onCartonSizeChange() {
  updateVolume()
  updateCartonSizeText()
  saveField('carton_length_cm', form.carton_length)
  saveField('carton_width_cm', form.carton_width)
  saveField('carton_height_cm', form.carton_height)
  saveField('carton_size', form.carton_size)
}

// 纸箱尺寸文本变化（带保存）
function onCartonSizeTextChange() {
  saveField('carton_size', form.carton_size)
}

function syncCartonCount() {
  const count = computedCartonCount.value
  form.carton_count = count > 0 ? count : undefined
}

function updateCartonSizeText() {
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  form.carton_size = l > 0 && w > 0 && h > 0 ? `${l}x${w}x${h}cm` : ''
}

// 更新打包规格
function updatePackSpec() {
  if (form.packaging === '多件/箱') {
    const upc = Number(form.units_per_carton || 0)
    form.pack_spec = upc > 0 ? `${upc} pcs/ctn` : ''
  } else if (form.packaging === '1件多箱') {
    const cpu = Number(form.cartons_per_unit || 0)
    form.pack_spec = cpu > 0 ? `1pcs/${cpu} ctn` : ''
  } else {
    form.pack_spec = '1 pcs/ctn'
  }
}

// 更新预估体积
function updateVolume() {
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  if (l > 0 && w > 0 && h > 0) {
    form.estimated_volume = (l * w * h) / 1000000
  } else {
    form.estimated_volume = undefined
  }
}

/**
 * 自动计算预估美金价（采购信息部分）
 *
 * 公式：
 *   - 人民币采购: 预估美金价 = 人民币采购价 × (1 + 毛利率) / 汇率
 *   - 美元采购:   预估美金价 = 美元采购价 × (1 + 毛利率)
 *
 * 当采购价、采购币种、毛利率、汇率任一变化时自动重算。
 */
watch(
  () => [
    form.purchase_price,
    form.purchase_currency,
    form.profit_margin,
    form.exchange_rate,
  ],
  () => {
    if (form.purchase_price == null) return
    const price = Number(form.purchase_price) || 0
    const margin = Number(form.profit_margin) || 0
    const rate = Number(form.exchange_rate) || 6.8
    const factor = 1 + margin / 100
    let usdPrice: number
    if (form.purchase_currency === 'USD') {
      usdPrice = price * factor
    } else {
      if (!rate) return
      usdPrice = (price * factor) / rate
    }
    form.estimated_usd_price = Math.round(usdPrice * 100) / 100
  },
  { immediate: true }
)

// 数量变化时同步更新总箱数（仅在包装方式为多件/箱或1件多箱时生效）
watch(
  () => form.quantity,
  () => {
    if (form.packaging === '多件/箱' || form.packaging === '1件多箱') {
      const count = computedCartonCount.value
      form.carton_count = count > 0 ? count : undefined
    }
  }
)

// 初始化时计算打包规格和体积
onMounted(() => {
  updatePackSpec()
  updateVolume()
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
  // 加载附图列表（从 localStorage 或 source）
  form.extra_images = loadExtraImages(source.id) || (source.image_url_2 ? [source.image_url_2] : [])
  form.product_name = source.product_name || ''
  form.product_name_en = source.product_name_en || ''
  form.product_feature = source.product_feature || ''
  // 产品需求/产品颜色以换行方式存入 remark 字段；读取时按换行拆出
  const remarkText = source.remark || ''
  const remarkLines = remarkText.split(/\r?\n/)
  const remarkRemainLines: string[] = []
  let parsedAcquires = ''
  let parsedColor = ''
  let inAcquires = false
  let inColor = false
  for (const line of remarkLines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('【产品需求】')) {
      inAcquires = true
      inColor = false
      const content = trimmed.replace('【产品需求】', '').trim()
      if (content) parsedAcquires = content
      continue
    }
    if (trimmed.startsWith('【产品颜色】')) {
      inColor = true
      inAcquires = false
      const content = trimmed.replace('【产品颜色】', '').trim()
      if (content) parsedColor = content
      continue
    }
    if (inAcquires) {
      parsedAcquires = parsedAcquires ? `${parsedAcquires}\n${line}` : line
    } else if (inColor) {
      parsedColor = parsedColor ? `${parsedColor}\n${line}` : line
    } else {
      remarkRemainLines.push(line)
    }
  }
  form.product_acquires = parsedAcquires || (source as any).product_acquires || ''
  form.product_color = parsedColor || (source as any).product_color || ''
  form.remark = remarkRemainLines.join('\n').trim()
  form.oe_number = source.oe_number || ''
  form.quantity = source.quantity || 0
  form.unit_price = source.unit_price || 0
  form.estimated_margin = source.estimated_margin ?? undefined
  form.estimated_usd_price = source.estimated_usd_price ?? undefined
  form.purchase_price = source.purchase_price || 0
  // 采购币种/汇率/毛利率优先从源数据读取，否则使用默认值
  form.purchase_currency = (source as any).purchase_currency === 'USD' ? 'USD' : 'RMB'
  form.exchange_rate = (source as any).exchange_rate || 6.8
  form.profit_margin = (source as any).profit_margin ?? 25
  form.misc_fee = source.misc_fee || 0
  form.shipping_fee = source.shipping_fee || 0
  form.invoice_status = source.invoice_status || ''
  form.invoice_type = (source as any).invoice_type || ''
  form.invoice_rate = (source as any).invoice_rate || ''
  form.factory_name = source.factory_name || ''
  form.shop_url = source.shop_url || ''
  form.product_detail = source.product_detail || ''
  form.purchase_option_name = source.purchase_option_name || ''
  form.payment_method = (source as any).payment_method || ''
  form.factory_deposit = source.factory_deposit ?? undefined
  form.factory_balance = source.factory_balance ?? undefined
  form.stock_in_quantity = source.stock_in_quantity || 0
  form.carton_count = source.carton_count ?? undefined
  form.total_weight = source.total_weight ?? undefined
  form.delivery_date = source.delivery_date || ''
  form.carton_size = source.carton_size || ''
  // 包装规格相关字段
  form.packaging = (source as any).packaging || '1件/箱'
  form.units_per_carton = (source as any).units_per_carton ?? undefined
  form.cartons_per_unit = (source as any).cartons_per_unit ?? (source as any).boxes_count ?? undefined
  form.pack_spec = (source as any).pack_spec || ''
  form.estimated_volume = (source as any).estimated_volume ?? undefined
  form.carton_gross_weight = (source as any).carton_gross_weight ?? undefined
  // 解析纸箱尺寸字符串回填到长宽高
  const size = parseCartonSize(source.carton_size || '')
  form.carton_length = size.l || ((source as any).carton_length ?? undefined)
  form.carton_width = size.w || ((source as any).carton_width ?? undefined)
  form.carton_height = size.h || ((source as any).carton_height ?? undefined)
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

function buildRemarkText(): string {
  const parts: string[] = []
  const acquires = (form.product_acquires || '').trim()
  const color = (form.product_color || '').trim()
  if (acquires) parts.push(`【产品需求】\n${acquires}`)
  if (color) parts.push(`【产品颜色】\n${color}`)
  const remark = (form.remark || '').trim()
  if (remark) parts.push(remark)
  return parts.join('\n')
}

function onRemarkBlur() {
  const text = buildRemarkText()
  saveField('remark', text)
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

// 上传附图（追加到列表）
async function handleExtraImageChange(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.extra_images.push(res.data.data.url)
      saveExtraImages()
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

// 移除附图
function removeExtraImage(idx: number) {
  form.extra_images.splice(idx, 1)
  saveExtraImages()
}

const EXTRA_IMAGES_KEY = 'pi_item_extra_images'

function loadExtraImages(itemId: number | undefined): string[] | null {
  if (!itemId) return null
  try {
    const raw = localStorage.getItem(`${EXTRA_IMAGES_KEY}_${itemId}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveExtraImages() {
  if (!item.value?.id) return
  try {
    localStorage.setItem(
      `${EXTRA_IMAGES_KEY}_${item.value.id}`,
      JSON.stringify(form.extra_images)
    )
  } catch (e) {
    console.warn('保存附图失败', e)
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
  max-height: calc(94vh - 100px);
  overflow-y: auto;
  padding-right: 4px;
}

.product-edit-dialog::-webkit-scrollbar {
  width: 8px;
}
.product-edit-dialog::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
}
.product-edit-dialog::-webkit-scrollbar-track {
  background: #e2f0d9;
}

.edit-section {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 10px;
  overflow: hidden;
}

.section-title {
  padding: 7px 12px;
  font-weight: 600;
  font-size: 13px;
}

.section-body {
  padding: 10px 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px 10px;
}

.form-grid.info-row-3 {
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 8px;
}

.form-grid.info-row-4 {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 8px;
}

.form-grid.info-row-4:last-child {
  margin-bottom: 0;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.form-item.wide {
  grid-column: span 2;
}

.form-item.half {
  grid-column: span 3;
}

.form-item.all {
  grid-column: span 6;
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

.form-item label,
.image-cell > label,
.names-block > label {
  font-size: 12px;
  color: #606266;
  line-height: 1.2;
}

.form-item label.required::before,
.image-cell > label.required::before,
.names-block > label.required::before {
  content: '*';
  color: #f56c6c;
}

/* 图片 + 名称紧凑行 */
.compact-image-name-row {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 8px;
}

.image-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.main-image-block {
  width: 80px;
  flex-shrink: 0;
}

.extra-image-block {
  width: 360px;
  flex-shrink: 0;
}
/* 采购信息统一表格布局（沿用价格-开票情况，扩展为 5 列多行） */
.purchase-cost-table {
  grid-column: span 6;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(7, 42px);
  border: 1px solid #222;
  border-radius: 0;
  overflow: hidden;
  background: #fff;
}

.purchase-cost-head {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2f0d9;
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  font-size: 13px;
  color: #303133;
  font-weight: 600;
}

.purchase-cost-head:last-of-type {
  border-right: none;
}

.purchase-cost-head.span-2 {
  grid-column: span 2;
}

.invoice-group-head {
  grid-column: span 2;
}

.purchase-cost-head.required::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.purchase-cost-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  min-width: 0;
}

.purchase-cost-cell:last-child {
  border-right: none;
}

.purchase-cost-cell.span-3 {
  grid-column: span 3;
}

.purchase-cost-cell.span-2 {
  grid-column: span 2;
}

.purchase-cost-cell :deep(.el-input-number),
.purchase-cost-cell :deep(.el-input__wrapper),
.purchase-cost-cell :deep(.field-input-wrapper) {
  width: 100%;
}

.purchase-cost-cell :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.purchase-cost-cell :deep(.el-input__inner) {
  font-size: 12px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
}

.amount-cell {
  font-size: 16px;
  color: #000;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.invoice-type-cell,
.invoice-rate-cell {
  padding: 0 6px;
}

.product-detail-cell {
  align-items: stretch;
  padding: 4px;
}

.detail-right {
  grid-row: span 2;
}

.detail-label-placeholder {
  background: #fff;
}

.payment-head,
.payment-cell {
  background: #c6e0b4;
}

.product-detail-cell :deep(.el-textarea),
.product-detail-cell :deep(.el-textarea__inner) {
  height: 100%;
  resize: none;
  border-radius: 0;
  border: none;
  padding: 0;
  box-shadow: none;
  font-size: 12px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
  background: transparent;
}

/* 销售细节统一表格 */
.sales-detail-table {
  grid-column: span 6;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: 48px 68px 56px;
  border: 1px solid #222;
  border-radius: 0;
  overflow: hidden;
  background: #fff;
}

.sales-summary-head,
.sales-summary-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #efb4bd;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  font-size: 15px;
  color: #000;
  font-family: 'Times New Roman', 'SimSun', serif;
  min-width: 0;
}

.sales-summary-head {
  justify-content: flex-start;
  padding-left: 4px;
}

.sales-summary-cell.span-2 {
  grid-column: span 2;
}

.sales-summary-cell :deep(.field-input-wrapper),
.sales-summary-cell :deep(.el-input__wrapper) {
  width: 100%;
  box-shadow: none !important;
  border-radius: 0;
  padding: 0 6px;
  background: transparent;
}

.sales-detail-head {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7dada;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  font-size: 13px;
  color: #303133;
  font-weight: 600;
  text-align: center;
  line-height: 1.3;
  padding: 0 4px;
}

.sales-detail-head:last-of-type {
  border-right: none;
}

.sales-detail-head.required::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.sales-detail-head.vertical-text {
  flex-direction: column;
  font-size: 14px;
  line-height: 1.15;
  letter-spacing: 2px;
  padding: 4px 0;
}

.sales-detail-head.vertical-text .vline {
  display: block;
}

.sales-detail-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  min-width: 0;
  background: #f7dada;
}

.sales-detail-cell:last-child {
  border-right: none;
}

.sales-detail-cell.span-2 {
  grid-column: span 2;
}

.sales-detail-cell.span-6 {
  grid-column: span 6;
}

.sales-detail-cell :deep(.el-input-number),
.sales-detail-cell :deep(.el-input__wrapper),
.sales-detail-cell :deep(.field-input-wrapper) {
  width: 100%;
}

.sales-detail-cell :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.sales-detail-cell :deep(.el-input__inner) {
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
}

/* 产品名称（中英文两行表格布局） */
.name-table-row {
  display: grid;
  grid-template-columns: 80px 1fr;
  grid-template-rows: 1fr 1fr;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  height: 100px;
  flex-shrink: 0;
}

.name-label {
  grid-row: 1 / 3;
  grid-column: 1;
  border-right: 1px solid #dcdfe6;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 12px;
  color: #606266;
  line-height: 1.3;
}

.name-label .required {
  color: #f56c6c;
  font-size: 14px;
}

.name-row-zh {
  grid-column: 2;
  grid-row: 1;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
}

.name-row-en {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  flex-direction: column;
}

.name-input-label {
  font-size: 11px;
  color: #909399;
  padding: 2px 6px 0;
  background: #fafbfc;
  line-height: 1.4;
}

.name-input-cell {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 6px;
}

.name-input-cell :deep(.el-input__wrapper),
.name-input-cell :deep(.field-input-wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
  width: 100%;
}

.name-input-cell :deep(.el-input__inner) {
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
  text-align: left;
}

/* 全局 small 尺寸 */
.form-item :deep(.el-input__wrapper),
.form-item :deep(.el-textarea__inner) {
  padding: 1px 8px;
  min-height: 26px;
}

.form-item :deep(.el-input__inner) {
  font-size: 12px;
  height: 26px;
  line-height: 26px;
}

.form-item :deep(.el-textarea__inner) {
  font-size: 12px;
  padding: 4px 8px;
}

.form-item :deep(.el-input-number) {
  width: 100%;
}

.form-item :deep(.el-input-number .el-input__inner) {
  font-size: 12px;
  height: 26px;
  line-height: 26px;
}

.form-item :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  font-size: 12px;
}

.form-item :deep(.el-date-editor) {
  --el-date-editor-height: 26px;
}

.form-hint {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

/* ============ 主图 80x80 ============ */
.image-uploader-main {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.image-uploader-main:hover {
  border-color: #409eff;
}

.preview-image-main {
  width: 80px;
  height: 80px;
  object-fit: cover;
  display: block;
}

/* ============ 包装规格表格 ============ */
.packaging-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 12px;
}

.packaging-table th,
.packaging-table td {
  border: 1px solid #dcdfe6;
  padding: 4px 6px;
  vertical-align: middle;
  text-align: center;
  background: #fff;
}

.packaging-table thead th {
  background: #f5f7fa;
  color: #606266;
  font-weight: 600;
  font-size: 12px;
  height: 32px;
}

.packaging-table .th-left {
  width: 110px;
}

.packaging-table .td-label {
  width: 110px;
  background: #fafafa;
}

.packaging-table .row-secondary td {
  background: #fafbfc;
}

.packaging-table .row-secondary-label {
  color: #606266;
  font-weight: 500;
}

.packaging-table .row-secondary-text {
  text-align: left;
  color: #606266;
  font-size: 12px;
  white-space: nowrap;
}

.packaging-table .row-secondary-text :deep(.el-input),
.packaging-table .row-secondary-text :deep(.el-input-number) {
  vertical-align: middle;
}

.pack-spec-cell {
  width: 100%;
}

.pack-spec-cell :deep(.el-input-number),
.pack-spec-cell :deep(.el-input) {
  width: 100%;
}

.packaging-table :deep(.el-input-number .el-input__inner),
.packaging-table :deep(.el-input__inner) {
  font-size: 12px;
  text-align: center;
  height: 26px;
  line-height: 26px;
}

.packaging-table :deep(.el-input__wrapper) {
  padding: 1px 6px;
  min-height: 26px;
}

/* ============ 附图 360x80 横向滚动 ============ */
.extra-images-scroll {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 360px;
  height: 80px;
  padding: 4px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #fafafa;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
}

.extra-images-scroll::-webkit-scrollbar {
  height: 6px;
}
.extra-images-scroll::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}
.extra-images-scroll::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.extra-image-item {
  position: relative;
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ebeef5;
  background: #fff;
  cursor: pointer;
}

.extra-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.extra-image-item .remove-icon {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.extra-image-item:hover .remove-icon {
  opacity: 1;
}

.extra-image-uploader {
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #fff;
  transition: border-color 0.2s;
}

.extra-image-uploader:hover {
  border-color: #409eff;
}

.image-placeholder-icon {
  font-size: 20px;
  color: #909399;
}

.archive-file-name {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}
</style>
