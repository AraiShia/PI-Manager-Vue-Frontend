<template>
  <!-- 产品管理新增/编辑对话框组件 (整合完整基础信息、供应商采购细节与纸箱规格) -->
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="95vw"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
    :before-close="requestClose"
    @closed="onClosed"
  >
    <div class="product-management-edit-dialog">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="product-form"
      >
        <!-- 1:1 复制 ProductEditDialog.vue:L14-L178 基础信息表格块 -->
        <div class="edit-section">
          <div class="section-title" style="background-color: #fde2e2; color: #c45650;">基础信息</div>
          <div class="section-body">
            <div class="basic-info-table">
              <!-- 客户型号 -->
              <div class="basic-info-label model-label required">客户型号<br /><span>Model</span></div>
              <div class="basic-info-cell model-cell emphasis-cell" data-required-field="customer_model">
                <FieldInput
                  v-model="form.customer_model"
                  :status="getFieldStatus('customer_model')"
                  :disabled="modelLocked"
                  @blur="onCustomerModelBlur"
                />
              </div>

              <!-- 我司产品编号 -->
              <div class="basic-info-label own-code-label">我司产品编号<br /><span>S.NO.</span></div>
              <div class="basic-info-cell own-code-cell">
                <FieldInput
                  v-model="form.factory_code"
                  :status="getFieldStatus('company_code')"
                  :disabled="formLocked"
                  @blur="saveField('company_code', form.factory_code)"
                />
              </div>

              <!-- 主图 -->
              <div
                class="basic-info-image main-image-cell"
                data-required-field="image_url"
                @contextmenu="onImageContextMenu($event, 'main')"
                @dblclick="onMainImageDblClick"
              >
                <el-upload
                  class="image-uploader-main"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleImageChange"
                >
                  <img v-if="form.image_url" :src="assetUrl(form.image_url)" class="preview-image-main" alt="主图" />
                  <span v-else class="image-placeholder-text"><el-icon><Plus /></el-icon>主图</span>
                </el-upload>
                <span v-if="!form.image_url" class="main-image-required-star">*</span>
              </div>

              <!-- 附图 -->
              <div class="basic-info-image extra-images-cell">
                <div class="extra-images-scroll">
                  <div
                    v-for="(img, idx) in form.extra_images"
                    :key="idx"
                    class="extra-image-item"
                    @contextmenu="onImageContextMenu($event, 'extra', idx)"
                    @dblclick="onExtraImageDblClick(img)"
                  >
                    <img :src="assetUrl(img)" alt="附图" />
                    <el-icon class="remove-icon" @click="removeExtraImage(idx)"><Close /></el-icon>
                  </div>
                  <el-upload
                    class="extra-image-uploader"
                    :auto-upload="false"
                    :show-file-list="false"
                    :on-change="handleExtraImageChange"
                  >
                    <span class="extra-image-placeholder">
                      <el-icon class="image-placeholder-icon"><Plus /></el-icon>
                      <span v-if="form.extra_images.length === 0" class="extra-image-placeholder-text">附图</span>
                    </span>
                  </el-upload>
                </div>
              </div>

              <!-- 产品名称 (中文 & 英文) -->
              <div class="basic-info-label pname-label required">产品名称<br /><span>P-Name</span></div>
              <div class="basic-info-cell product-name-zh" data-required-field="product_name">
                <el-input
                  v-model="form.product_name"
                  :disabled="formLocked"
                  placeholder="中文名称"
                  @blur="saveField('detail_desc', form.product_name)"
                />
              </div>
              <div class="basic-info-cell product-name-en">
                <FieldInput
                  v-model="form.product_name_en"
                  :status="getFieldStatus('detail_desc_en')"
                  :disabled="formLocked"
                  placeholder="英文名称"
                  @blur="saveField('detail_desc_en', form.product_name_en)"
                />
              </div>

              <!-- 产品简称 (中文 & 英文) -->
              <div class="basic-info-label short-name-label">产品简称<br /><span>P-Name</span></div>
              <div class="basic-info-cell short-name-zh">
                <FieldInput
                  v-model="form.product_short_name"
                  :status="getFieldStatus('product_short_name')"
                  placeholder="中文简称"
                  @blur="saveField('product_short_name', form.product_short_name)"
                />
              </div>
              <div class="basic-info-cell short-name-en">
                <FieldInput
                  v-model="form.product_short_name_en"
                  :status="getFieldStatus('product_short_name_en')"
                  placeholder="英文简称"
                  @blur="saveField('product_short_name_en', form.product_short_name_en)"
                />
              </div>

              <!-- OE号列表 -->
              <div class="basic-info-label oe-label">OE号列表<br /><span>OE-NO.</span></div>
              <div class="basic-info-cell oe-cell">
                <el-input
                  v-model="form.oe_number"
                  type="textarea"
                  :rows="1"
                  resize="none"
                  placeholder="多编号逗号或换行分隔"
                  @blur="saveField('oe_number', form.oe_number)"
                />
              </div>

              <!-- 编号备注 -->
              <div class="basic-info-label remark-label">编号备注</div>
              <div class="basic-info-cell remark-cell">
                <el-input
                  v-model="form.product_code"
                  type="textarea"
                  :rows="1"
                  resize="none"
                  placeholder="编号备注信息"
                  @blur="saveField('customer_code', form.product_code)"
                />
              </div>

              <!-- 产品要求 -->
              <div class="basic-info-label details-label">产品要求<br /><span>P-Details</span></div>
              <div class="basic-info-cell details-cell">
                <FieldInput
                  v-model="form.product_acquires"
                  :status="getFieldStatus('product_acquires')"
                  placeholder="产品要求参数"
                  @blur="saveField('product_acquires', form.product_acquires)"
                />
              </div>

              <!-- 产品颜色 -->
              <div class="basic-info-label color-label">产品颜色<br /><span>P-color</span></div>
              <div class="basic-info-cell color-cell">
                <FieldInput
                  v-model="form.product_color"
                  :status="getFieldStatus('product_color')"
                  placeholder="产品颜色"
                  @blur="saveField('product_color', form.product_color)"
                />
              </div>

              <!-- 产品类别 (两级联动 Select) -->
              <div class="basic-info-label category-label required">产品类别<br /><span>P-Category</span></div>
              <div class="basic-info-cell category-cell" data-required-field="category_id">
                <div class="category-select-group">
                  <el-select
                    v-model="categoryLevel1"
                    placeholder="大类"
                    :disabled="categoryLocked || formLocked"
                    @change="onCategoryLevel1Change"
                  >
                    <el-option label="-- 请选择大类 --" value="" />
                    <el-option
                      v-for="category in parentCategories"
                      :key="category.code"
                      :label="category.name"
                      :value="category.code"
                    />
                  </el-select>
                  <el-select
                    v-model="categoryLevel2"
                    placeholder="子类"
                    :disabled="categoryLocked || formLocked || !categoryLevel1"
                    @change="onCategoryLevel2Change"
                  >
                    <el-option label="-- 请选择子类 --" value="" />
                    <el-option
                      v-for="category in childCategoryOptions"
                      :key="category.code"
                      :label="category.name"
                      :value="category.code"
                    />
                  </el-select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 扩展信息分块 (价格与采购信息表格块，7行7列均分精细排版) -->
        <div class="edit-section" style="margin-top: 10px;">
          <div class="section-title" style="background-color: #fde2d8; color: #b85c38;">价格与采购信息</div>
          <div class="section-body">
            <div class="purchase-cost-table-custom">
              <!-- 行1：报价 USD / 人民币采购价 / 贴标费 / 运费 表头 + 供应商选择 + 开票情况 -->
              <div class="table-head cell-quote-head required">
                * 报价<br />PRICE/USD
              </div>
              <div class="table-head cell-rmb-price-head required">
                * 人民币采购价
              </div>
              <div class="table-head cell-labeling-head">
                贴标费
              </div>
              <div class="table-head cell-shipping-head">
                运费
              </div>
              <div class="table-head cell-supplier-head required">
                * 供应商
              </div>
              <div class="table-cell cell-supplier-content" data-required-field="supplier_name">
                <SupplierSearchSelect
                  v-model="form.supplier"
                  :current-name="form.supplier_name"
                  :disabled="formLocked"
                  placeholder="搜索或选择供应商"
                  @select="onSupplierSelect"
                  @clear="onSupplierClear"
                >
                  <template #empty-extra="{ keyword }">
                    <div v-if="keyword" class="ss-extra-actions">
                      <el-button
                        type="primary"
                        size="small"
                        link
                        @click="openNewSupplierDialog"
                      >
                        + 新建供应商「{{ keyword }}」
                      </el-button>
                    </div>
                  </template>
                </SupplierSearchSelect>
              </div>
              <div class="table-head cell-invoice-group-head">
                开票情况
              </div>

              <!-- 行2：报价 USD 数值 / 人民币采购价数值 / 贴标费数值 / 运费数值 + 供应商链接 + 开票类型 & 备注 -->
              <div class="table-cell cell-quote-val">
                <el-input-number
                  v-model="form.price_usd"
                  :min="0"
                  :precision="2"
                  class="full-width"
                  placeholder="0.00"
                >
                  <template #prefix>$</template>
                </el-input-number>
              </div>
              <div class="table-cell cell-rmb-price-val">
                <el-input-number
                  v-model="form.price_rmb"
                  :min="0"
                  :precision="2"
                  class="full-width"
                  placeholder="0.00"
                >
                  <template #prefix>¥</template>
                </el-input-number>
              </div>
              <div class="table-cell cell-labeling-val">
                <el-input-number
                  v-model="form.labeling_fee"
                  :precision="2"
                  class="full-width"
                  placeholder="0.00"
                >
                  <template #prefix>¥</template>
                </el-input-number>
              </div>
              <div class="table-cell cell-shipping-val">
                <el-input-number
                  v-model="form.shipping_fee"
                  :precision="2"
                  class="full-width"
                  placeholder="0.00"
                >
                  <template #prefix>¥</template>
                </el-input-number>
              </div>
              <div class="table-head cell-shop-url-head">
                供应商链接:
              </div>
              <div class="table-cell cell-shop-url-content">
                <el-select
                  v-model="form.shop_url"
                  filterable
                  allow-create
                  default-first-option
                  :clearable="!formLocked"
                  placeholder="选择或输入 1688 链接"
                  style="flex: 1; min-width: 0;"
                  @change="onShopUrlChange"
                  @clear="onShopUrlClear"
                >
                  <el-option
                    v-for="u in supplierUrlOptions"
                    :key="u.id || u.url"
                    :label="u.display_name ? `${u.display_name} (${u.url})` : u.url"
                    :value="u.url"
                  >
                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 12px;">
                      <span style="font-weight: 500; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 60%;">
                        {{ u.display_name || u.url }}
                      </span>
                      <span style="color: #909399; font-size: 11px; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 38%;">
                        {{ u.url }}
                      </span>
                    </div>
                  </el-option>
                </el-select>
                <el-tooltip content="打开网页链接" placement="top" :disabled="!form.shop_url">
                  <el-button
                    type="primary"
                    link
                    :disabled="!form.shop_url"
                    style="padding: 0 4px;"
                    @click="openShopUrl"
                  >
                    <el-icon :size="16"><TopRight /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
              <div class="table-cell cell-invoice-type">
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


              <!-- 行3a/3b：产品特性 (跨两子行 1-4列) + 采购方式/付款方式 (5-6列) + 开票工厂/货源地 (7-8列) -->
              <div class="table-head cell-product-detail-head required">
                * 产品特性/<br />选项/采购备注
              </div>
              <div class="table-cell cell-product-detail-content" data-required-field="product_detail">
                <el-input
                  v-model="form.product_detail"
                  type="textarea"
                  :rows="4"
                  resize="none"
                  :disabled="formLocked"
                  placeholder="产品特性说明"
                  @blur="saveField('product_detail', form.product_detail)"
                />
              </div>

              <div class="table-head cell-purchase-option-head">采购方式:</div>
              <div class="table-cell cell-purchase-option-content">
                <FieldInput
                  v-model="form.purchase_option_name"
                  :status="getFieldStatus('purchase_option_name')"
                  :disabled="formLocked"
                  placeholder="1688/微信联系/线下合同"
                  @blur="saveField('purchase_option_name', form.purchase_option_name)"
                />
              </div>
              <div class="table-head cell-factory-invoice-head">开票工厂（全称）：</div>
              <div class="table-cell cell-factory-invoice-content">
                <FieldInput
                  v-model="form.factory_invoice_name"
                  :status="getFieldStatus('factory_invoice_name')"
                  :disabled="!invoiceFactoryEnabled"
                  :placeholder="factoryInvoicePlaceholder"
                  @blur="invoiceFactoryEnabled && onUnmappedBlur('factory_invoice_name')"
                />
              </div>

              <div class="table-head cell-payment-method-head">付款方式:</div>
              <div class="table-cell cell-payment-method-content">
                <FieldInput
                  v-model="form.payment_method"
                  :status="getFieldStatus('payment_method')"
                  placeholder="1688线上支付、人民币"
                  @blur="saveField('payment_method', form.payment_method)"
                />
              </div>
              <div class="table-head cell-source-place-head">货源地</div>
              <div class="table-cell cell-source-place-content">
                <FieldInput
                  v-model="form.source_place"
                  :status="getFieldStatus('source_place')"
                  placeholder="如：霸州"
                  @blur="onUnmappedBlur('source_place')"
                />
              </div>

              <!-- 行4 & 行5：纸箱包装与规格 (8 列对齐) -->
              <div class="table-head cell-carton-pack-head required">
                * 纸箱包装：<br /><span style="font-size:10px;color:#909399;font-weight:normal;">长×宽×高 (cm)</span>
              </div>
              <div class="table-head cell-pack-spec-head required">
                * 打包规格
              </div>
              <div class="table-head cell-carton-gross-weight-head">
                整箱毛重
              </div>
              <div class="table-head cell-estimated-volume-head">
                预估体积
              </div>
              <div class="table-head cell-estimated-gross-weight-head">
                预估毛重
              </div>

              <div class="table-cell cell-carton-length" data-required-field="carton_length">
                <el-input v-model="form.carton_length" placeholder="长" type="number" :disabled="formLocked" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="table-cell cell-carton-width" data-required-field="carton_width">
                <el-input v-model="form.carton_width" placeholder="宽" type="number" :disabled="formLocked" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="table-cell cell-carton-height" data-required-field="carton_height">
                <el-input v-model="form.carton_height" placeholder="高" type="number" :disabled="formLocked" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="table-cell cell-pack-spec-content" data-required-field="pack_spec">
                <el-popover v-if="!formLocked" ref="packSpecPopoverRef" placement="bottom" :width="260" trigger="click">
                  <template #reference>
                    <el-input :model-value="form.pack_spec || '1pcs/1ctn'" readonly style="width: 100%" />
                  </template>
                  <template #default>
                    <div class="pack-spec-popover">
                      <el-radio-group v-model="form.packaging" @change="onPackagingChange">
                        <el-radio value="1件/箱">1件/箱</el-radio>
                        <el-radio value="多件/箱">多件/箱</el-radio>
                        <el-radio value="1件多箱">1件多箱</el-radio>
                      </el-radio-group>
                      <el-input-number
                        v-if="form.packaging === '多件/箱'"
                        v-model="form.units_per_carton"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updatePackSpec"
                        @blur="onPackSpecBlur"
                      />
                      <el-input-number
                        v-else-if="form.packaging === '1件多箱'"
                        v-model="form.cartons_per_unit"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updatePackSpec"
                        @blur="onPackSpecBlur"
                      />
                      <el-button size="small" type="primary" style="width: 100%" @click="onPackSpecBlur">确定</el-button>
                    </div>
                  </template>
                </el-popover>
                <span v-else class="pack-spec-locked">{{ form.pack_spec || '1pcs/1ctn' }}</span>
              </div>
              <div class="table-cell cell-carton-gross-weight-content">
                <el-input v-model="form.carton_gross_weight" type="number" :disabled="formLocked" style="width: 100%" @change="saveField('carton_gross_weight', form.carton_gross_weight)" />
              </div>
              <div class="table-cell cell-estimated-volume-content">
                <el-input :model-value="form.estimated_volume != null ? form.estimated_volume.toFixed(6) : ''" readonly />
              </div>
              <div class="table-cell cell-estimated-gross-weight-content">
                <el-input :model-value="estimatedGrossWeight" readonly />
              </div>
            </div>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 底部操作按钮区域 -->
    <template #footer>
      <div class="dialog-footer-content">
        <el-button @click="requestClose()">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProduct">保存</el-button>
      </div>
    </template>

    <!-- 新建供应商弹窗 -->
    <SupplierFormDialog
      v-model="newSupplierDialogVisible"
      :supplier="null"
      @success="onNewSupplierCreated"
    />
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @file ProductManagementEditDialog.vue
 * @description 产品管理 - 新增/编辑产品独立弹窗组件 (完美对齐 ProductEditDialog.vue 完整表格字段与供应商/纸箱逻辑)
 * @author Antigravity Architect Team
 */

import { ref, reactive, computed, onMounted, onBeforeUnmount, toRaw } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { Plus, Close, TopRight } from '@element-plus/icons-vue'
import { assetUrl } from '@/api/base'
import {
  productsApi,
  type CustomerOption,
  type CustomerProduct,
  type ProductFormPayload
} from '@/api/products'
import {
  FALLBACK_PARENT_CATEGORIES,
  FALLBACK_CHILD_CATEGORIES
} from '@/constants/productCategories'
import { suppliersApi, type Supplier, pendingSupplierState } from '@/api/suppliers'
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'
import SupplierFormDialog from '@/components/supplier/SupplierFormDialog.vue'
import SupplierSearchSelect from '@/components/common/SupplierSearchSelect.vue'
import FieldInput from '@/components/order/FieldInput.vue'
import type { FieldStatus } from '@/composables/useProductEdit'

/** 组件 Props 定义 */
interface Props {
  /** 外部传入的客户下拉列表 */
  customers?: CustomerOption[]
  /** 外部传入的类别下拉列表 */
  categories?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  customers: () => [],
  categories: () => []
})

/** 组件 Emits 定义 */
const emit = defineEmits<{
  (e: 'success', product: CustomerProduct | null): void
  (e: 'closed'): void
}>()

// ================= 响应式状态声明 =================

/** 对话框显隐状态 */
const visible = ref<boolean>(false)

/** 脏数据比对使用的表单初始状态深快照 */
const initialFormSnapshot = ref<string>('')

/** 表单提交 loading 状态 */
const saving = ref<boolean>(false)

/** 当前正在编辑的产品对象，为 null 时表示新增 */
const editingProduct = ref<CustomerProduct | null>(null)

/** 表单 Instance 引用 */
const formRef = ref<FormInstance>()

/** 锁定控制变量 */
const modelLocked = ref<boolean>(false)
const formLocked = ref<boolean>(false)
const categoryLocked = ref<boolean>(false)

/** 大类选中 Code */
const categoryLevel1 = ref<string>('')

/** 子类选中 Code */
const categoryLevel2 = ref<string>('')

/** 供应商 URL 下拉选项 */
const supplierUrlOptions = ref<ProductSupplierUrl[]>([])
const initialShopUrl = ref<string>('')
let userEditedShopUrl = false
let isConfirmingUrlClear = false

/** 新建供应商弹窗显隐 */
const newSupplierDialogVisible = ref<boolean>(false)

/** 打包规格 Popover 引用 */
const packSpecPopoverRef = ref()

/** 内部自动加载的客户与分类列表 */
const internalCustomers = ref<CustomerOption[]>([])
const internalCategories = ref<any[]>([])

/** 扩展表单数据结构 */
interface ExtendedProductForm extends ProductFormPayload {
  factory_code?: string
  product_name_en?: string
  product_short_name?: string
  product_short_name_en?: string
  oe_number?: string
  product_code?: string
  product_acquires?: string
  product_color?: string
  extra_images: string[]
  product_detail?: string
  supplier_name?: string
  supplier?: Supplier | null
  shop_url?: string
  invoice_type?: string
  invoice_rate?: string
  purchase_option_name?: string
  payment_method?: string
  factory_invoice_name?: string
  source_place?: string
  carton_length?: number | undefined
  carton_width?: number | undefined
  carton_height?: number | undefined
  carton_size?: string
  packaging?: '1件/箱' | '多件/箱' | '1件多箱'
  units_per_carton?: number | undefined
  cartons_per_unit?: number | undefined
  pack_spec?: string
  carton_gross_weight?: number | undefined
  estimated_volume?: number | undefined
  labeling_fee?: number | undefined
  shipping_fee?: number | undefined
}

/** 空表单默认结构 */
const emptyForm = (): ExtendedProductForm => ({
  customer_id: undefined as unknown as number,
  product_name: '',
  product_name_en: '',
  product_short_name: '',
  product_short_name_en: '',
  customer_model: '',
  factory_code: '',
  color: '',
  product_color: '',
  customer_remark: '',
  category_id: '',
  price_usd: null,
  price_rmb: null,
  detail_desc: '',
  brand: '',
  specifications: '',
  image_url: '',
  extra_images: [],
  sub_images: [],
  oe_number: '',
  product_code: '',
  product_acquires: '',
  product_detail: '',
  supplier_name: '',
  supplier: null,
  shop_url: '',
  invoice_type: '',
  invoice_rate: '',
  purchase_option_name: '',
  payment_method: '',
  factory_invoice_name: '',
  source_place: '',
  carton_length: undefined,
  carton_width: undefined,
  carton_height: undefined,
  carton_size: '',
  packaging: '1件/箱',
  units_per_carton: undefined,
  cartons_per_unit: undefined,
  pack_spec: '',
  carton_gross_weight: undefined,
  estimated_volume: undefined,
  labeling_fee: 0,
  shipping_fee: 0,
  codes: [],
  oes: []
})

/** 表单响应式数据对象 */
const form = reactive<ExtendedProductForm>(emptyForm())

/** 表单校验规则 */
const rules: FormRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }]
}

// ================= 计算属性计算 =================

/** 动态对话框标题 (参考 ProductEditDialog.vue) */
const dialogTitle = computed(() => {
  const actionText = editingProduct.value ? '编辑产品' : '新增产品'
  const modelOrName = form.customer_model || form.factory_code || form.product_name || ''
  const matchedCustomer = customerOptions.value.find(c => c.id === form.customer_id)
  const customerStr = matchedCustomer
    ? customerName(matchedCustomer)
    : (form.customer_id ? `客户#${form.customer_id}` : '')

  const parts = [actionText]
  if (modelOrName) parts.push(modelOrName)
  if (customerStr) parts.push(customerStr)
  return parts.join(' - ')
})

/** 最终使用的客户选项列表 */
const customerOptions = computed<CustomerOption[]>(() => {
  return props.customers.length ? props.customers : internalCustomers.value
})

/** 最终使用的类别选项列表 */
const categoryOptions = computed<any[]>(() => {
  return props.categories.length ? props.categories : internalCategories.value
})

/** 顶层大类选项 */
const parentCategories = computed(() => {
  return categoryOptions.value.filter((c: any) => !c.parent_id)
})

/** 二级子类选项 */
const childCategoryOptions = computed(() => {
  if (!categoryLevel1.value) return []
  return categoryOptions.value.filter((c: any) => c.parent_id === categoryLevel1.value)
})

/** 开票工厂全称激活判断 */
const invoiceFactoryEnabled = computed(() => form.invoice_type === '增票' || form.invoice_type === '普票')

/** 开票工厂全称动态提示词 (未选择增票/普票时提醒) */
const factoryInvoicePlaceholder = computed<string>(() => {
  if (invoiceFactoryEnabled.value) {
    return '开票工厂全称'
  }
  return form.invoice_type === '不开票' ? '未选择开票' : '未选择开票类型'
})

/** 预估毛重计算 */
const estimatedGrossWeight = computed(() => {
  const gw = Number(form.carton_gross_weight || 0)
  if (!gw) return ''
  const unitsPerCarton = form.packaging === '多件/箱'
    ? Number(form.units_per_carton || 0)
    : form.packaging === '1件多箱'
    ? Number(form.cartons_per_unit || 0)
    : 1
  if (unitsPerCarton > 0) {
    return (gw / unitsPerCarton).toFixed(2)
  }
  return gw.toFixed(2)
})

// ================= 辅助/交互函数 =================

function getFieldStatus(_field: string): FieldStatus {
  return 'idle'
}

function saveField(_field: string, _value: any): void {}

function onCustomerModelBlur(): void {}

function onUnmappedBlur(_field: string): void {}

function onImageContextMenu(event: MouseEvent, _type: string, _index?: number): void {
  event.preventDefault()
}

function onMainImageDblClick(): void {}

function onExtraImageDblClick(_img: string): void {}

/** 打开网页链接 */
function openShopUrl(): void {
  if (!form.shop_url) return
  let target = form.shop_url.trim()
  if (!/^https?:\/\//i.test(target)) {
    target = `https://${target}`
  }
  window.open(target, '_blank', 'noopener,noreferrer')
}

/** 大类发生变化时重置子类并同步 category_id */
function onCategoryLevel1Change(): void {
  categoryLevel2.value = ''
  form.category_id = categoryLevel1.value || ''
}

/** 子类发生变化时同步 category_id */
function onCategoryLevel2Change(): void {
  form.category_id = categoryLevel2.value || categoryLevel1.value || ''
}

/** 格式化获取客户显示名称 */
function customerName(item: CustomerOption): string {
  return item.customer_name || item.name || item.customer_code || `客户#${item.id}`
}

/** 分割解析多值文本 */
function splitList(value: string): string[] {
  if (!value) return []
  return value
    .split(/[\n,，;；]+/)
    .map(item => item.trim())
    .filter(Boolean)
}

/** 重置/批量赋值表单字段 */
function assignForm(payload: Partial<ExtendedProductForm>): void {
  Object.assign(form, emptyForm(), payload)
}

/** 主图选择回调 */
function handleImageChange(uploadFile: UploadFile): void {
  if (uploadFile.raw) {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        form.image_url = e.target.result as string
      }
    }
    reader.readAsDataURL(uploadFile.raw)
  }
}

/** 附图选择回调 */
function handleExtraImageChange(uploadFile: UploadFile): void {
  if (uploadFile.raw) {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        if (!form.extra_images) form.extra_images = []
        form.extra_images.push(e.target.result as string)
      }
    }
    reader.readAsDataURL(uploadFile.raw)
  }
}

/** 删除某张附图 */
function removeExtraImage(index: number): void {
  if (form.extra_images) {
    form.extra_images.splice(index, 1)
  }
}

// ================= 供应商与 1688 链接逻辑 =================

async function onSupplierSelect(s: Supplier): Promise<void> {
  form.supplier_name = s.supplier_name
  form.supplier = s
  const platformMap: Record<string, string> = {
    '1688': '1688平台采购',
    'wechat': '微信采购',
    'online': '线上采购',
    'offline': '线下采购',
  }
  form.purchase_option_name = platformMap[(s as any).platform] || '1688平台采购'
  pendingSupplierState.supplier = s
  pendingSupplierState.platform = (s.platform as any) || '1688'
  pendingSupplierState.wechat_id = s.wechat_id || null
  pendingSupplierState.wechat_nickname = s.wechat_nickname || null

  await loadSupplierUrls()
  applyShopUrlFromPriority()
}

function onSupplierClear(): void {
  form.supplier_name = ''
  form.supplier = null
  supplierUrlOptions.value = []
  userEditedShopUrl = false
}

function openNewSupplierDialog(): void {
  newSupplierDialogVisible.value = true
}

async function onNewSupplierCreated(created: Supplier): Promise<void> {
  const name = created?.supplier_name ?? form.supplier_name
  if (name) form.supplier_name = name
  if (created) {
    form.supplier = created
    const platformMap: Record<string, string> = {
      '1688': '1688平台采购',
      'wechat': '微信采购',
      'online': '线上采购',
      'offline': '线下采购',
    }
    form.purchase_option_name = platformMap[(created as any).platform] || '1688平台采购'
  }
  await loadSupplierUrls()
  applyShopUrlFromPriority()
}

async function loadSupplierUrls(): Promise<void> {
  const pid = editingProduct.value?.id
  if (!pid) { supplierUrlOptions.value = []; return }
  const rawId = (form.supplier as any)?.id
  const supplierId = rawId && rawId > 0 ? rawId : null
  const supplierName = form.supplier_name || null
  try {
    const res = await productSupplierUrlsApi.list(pid, supplierId, supplierName)
    let options = Array.isArray(res) ? [...res] : []
    if (options.length === 0) {
      const allRes = await productSupplierUrlsApi.list(pid, null, null)
      if (Array.isArray(allRes) && allRes.length > 0) {
        options = [...allRes]
      }
    }
    if (form.shop_url && !options.some((u) => u.url === form.shop_url)) {
      options.unshift({
        id: 0,
        product_id: pid,
        supplier_id: supplierId,
        supplier_name: form.supplier_name || '',
        url: form.shop_url,
        display_name: null,
        is_default: false,
        created_at: '',
      })
    }
    supplierUrlOptions.value = options
  } catch { supplierUrlOptions.value = [] }
}

async function onShopUrlClear(): Promise<void> {
  const previousUrl = initialShopUrl.value || form.shop_url
  if (!previousUrl) {
    form.shop_url = ''
    initialShopUrl.value = ''
    return
  }
  isConfirmingUrlClear = true
  try {
    await ElMessageBox.confirm('确认要清空当前供应商链接吗？', '清空链接确认', {
      confirmButtonText: '确认清空',
      cancelButtonText: '取消',
      type: 'warning',
    })
    form.shop_url = ''
    initialShopUrl.value = ''
    userEditedShopUrl = true
    ElMessage.success('已清空供应商链接')
  } catch {
    form.shop_url = previousUrl
  } finally {
    isConfirmingUrlClear = false
  }
}

function onShopUrlChange(url: string): void {
  if (isConfirmingUrlClear) return
  userEditedShopUrl = true
  if (!url) {
    onShopUrlClear()
    return
  }
  initialShopUrl.value = url
}

function applyShopUrlFromPriority(): void {
  if (userEditedShopUrl) return
  if (initialShopUrl.value) {
    form.shop_url = initialShopUrl.value
    return
  }
  const defaultUrl = supplierUrlOptions.value.find(u => u.is_default)
  if (defaultUrl) {
    form.shop_url = defaultUrl.url
    return
  }
  if (supplierUrlOptions.value.length > 0) {
    form.shop_url = supplierUrlOptions.value[0].url
  }
}

// ================= 纸箱规格与体积逻辑 =================

function updateVolume(): void {
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  if (l > 0 && w > 0 && h > 0) {
    const cartonVolume = (l * w * h) / 1000000
    const unitsPerCarton = form.packaging === '多件/箱'
      ? Number(form.units_per_carton || 0)
      : form.packaging === '1件多箱'
      ? Number(form.cartons_per_unit || 0)
      : 1
    if (unitsPerCarton > 0) {
      form.estimated_volume = (cartonVolume / unitsPerCarton)
    } else {
      form.estimated_volume = cartonVolume
    }
  } else {
    form.estimated_volume = undefined
  }
}

function updatePackSpec(): void {
  if (form.packaging === '多件/箱') {
    const upc = Number(form.units_per_carton || 0)
    form.pack_spec = upc > 0 ? `${upc}pcs/1ctn` : ''
  } else if (form.packaging === '1件多箱') {
    const cpu = Number(form.cartons_per_unit || 0)
    form.pack_spec = cpu > 0 ? `1pcs/${cpu}ctn` : ''
  } else {
    form.pack_spec = '1pcs/1ctn'
  }
}

function onPackagingChange(): void {
  if (form.packaging === '多件/箱') {
    form.units_per_carton = form.units_per_carton || 1
    form.cartons_per_unit = undefined
  } else if (form.packaging === '1件多箱') {
    form.units_per_carton = undefined
    form.cartons_per_unit = form.cartons_per_unit || 1
  } else {
    form.units_per_carton = undefined
    form.cartons_per_unit = undefined
  }
  updatePackSpec()
  updateVolume()
}

function onCartonSizeChange(): void {
  updateVolume()
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  form.carton_size = l > 0 && w > 0 && h > 0 ? `${l}x${w}x${h}cm` : ''
}

function onPackSpecBlur(): void {
  updatePackSpec()
  updateVolume()
  packSpecPopoverRef.value?.hide()
}

/** 自动加载选项数据 */
async function loadOptionsIfNeeded(): Promise<void> {
  if (!props.customers.length && internalCustomers.value.length === 0) {
    try {
      const customerRes = await productsApi.customers()
      internalCustomers.value = customerRes.data || []
    } catch (e) {
      console.error('[ProductManagementEditDialog] 获取客户下拉列表失败:', e)
    }
  }

  if (!props.categories.length && internalCategories.value.length === 0) {
    try {
      const categoryRes = await productsApi.categories()
      const cats = categoryRes.data || []
      internalCategories.value = cats.length
        ? cats
        : [...FALLBACK_PARENT_CATEGORIES, ...FALLBACK_CHILD_CATEGORIES]
    } catch (e) {
      console.error('[ProductManagementEditDialog] 获取类别下拉列表失败:', e)
      internalCategories.value = [
        ...FALLBACK_PARENT_CATEGORIES,
        ...FALLBACK_CHILD_CATEGORIES
      ]
    }
  }
}

// ================= 快照对比与未保存离开 Guard =================

/**
 * 创建表单与选定分类状态的序列化快照 JSON 字符串
 * @returns 序列化快照字符串
 */
function createFormSnapshot(): string {
  return JSON.stringify({
    form: toRaw(form),
    categoryLevel1: categoryLevel1.value,
    categoryLevel2: categoryLevel2.value
  })
}

/**
 * 计算属性：对比初始快照，判断当前表单是否存在未保存的更动
 */
const hasUnsavedChanges = computed<boolean>(() => {
  if (!visible.value) return false
  return createFormSnapshot() !== initialFormSnapshot.value
})

/**
 * 对话框关闭前确认拦截器
 * 若检测到未保存改动，弹出双重二次确认弹窗防误触丢失数据
 * @param done el-dialog :before-close 传入的组件关闭完成回调函数
 */
async function requestClose(done?: () => void): Promise<void> {
  if (!hasUnsavedChanges.value) {
    if (typeof done === 'function') {
      done()
    } else {
      close()
    }
    return
  }

  try {
    await ElMessageBox.confirm(
      '当前产品编辑内容还有未保存的改动，关闭后这些改动可能丢失。是否继续关闭？',
      '未保存提示',
      {
        confirmButtonText: '继续关闭',
        cancelButtonText: '返回编辑',
        type: 'warning'
      }
    )
    await ElMessageBox.confirm(
      '请再次确认：仍然关闭并放弃未保存改动吗？',
      '二次确认',
      {
        confirmButtonText: '确认关闭',
        cancelButtonText: '返回编辑',
        type: 'warning'
      }
    )
    initialFormSnapshot.value = createFormSnapshot()
    if (typeof done === 'function') {
      done()
    } else {
      close()
    }
  } catch {
    // 用户选择返回编辑，取消关闭
  }
}

/**
 * 监听浏览器窗口关闭或刷新事件，有脏数据时弹出原生拦截提示
 */
function onBeforeUnload(event: BeforeUnloadEvent): void {
  if (!hasUnsavedChanges.value) return
  event.preventDefault()
  event.returnValue = ''
}

// 挂载与卸载组件时管理浏览器全局 BeforeUnload 防误触事件
onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})

// ================= 组件暴露 API 方法 =================

/**
 * 打开对话框（暴露给父组件调用）
 * @param product 产品对象，为 null 时为新增模式
 * @param customerId 可选的默认客户 ID
 */
async function open(product: CustomerProduct | null = null, customerId?: number): Promise<void> {
  editingProduct.value = product
  await loadOptionsIfNeeded()

  if (product) {
    // 编辑模式：赋值与回填
    assignForm({
      customer_id: product.customer_id,
      product_name: product.product_name || '',
      product_name_en: (product as any).product_name_en || '',
      product_short_name: (product as any).product_short_name || '',
      product_short_name_en: (product as any).product_short_name_en || '',
      customer_model: product.customer_model || '',
      factory_code: (product as any).factory_code || (product as any).product_code || '',
      color: product.color || '',
      product_color: product.color || '',
      customer_remark: product.customer_remark || '',
      category_id: product.category_id || '',
      price_usd: product.price_usd ?? null,
      price_rmb: product.price_rmb ?? null,
      detail_desc: product.detail_desc || '',
      brand: product.brand || '',
      specifications: product.specifications || '',
      image_url: product.image_url || '',
      extra_images: product.sub_images ? [...product.sub_images] : [],
      product_detail: (product as any).product_detail || '',
      supplier_name: (product as any).supplier_name || '',
      shop_url: (product as any).shop_url || '',
      invoice_type: (product as any).invoice_type || '',
      invoice_rate: (product as any).invoice_rate || '',
      purchase_option_name: (product as any).purchase_option_name || '',
      payment_method: (product as any).payment_method || '',
      factory_invoice_name: (product as any).factory_invoice_name || '',
      source_place: (product as any).source_place || '',
      carton_length: (product as any).carton_length ?? undefined,
      carton_width: (product as any).carton_width ?? undefined,
      carton_height: (product as any).carton_height ?? undefined,
      packaging: (product as any).packaging || '1件/箱',
      units_per_carton: (product as any).units_per_carton ?? undefined,
      cartons_per_unit: (product as any).cartons_per_unit ?? undefined,
      pack_spec: (product as any).pack_spec || '',
      carton_gross_weight: (product as any).carton_gross_weight ?? undefined,
      estimated_volume: (product as any).estimated_volume ?? undefined
    })

    // OE 号回填
    if (product.oes && product.oes.length) {
      form.oe_number = product.oes.map(o => o.oe_number).join('\n')
    }

    // 回填类别两级下拉选
    if (product.category_id) {
      const cat = categoryOptions.value.find((c: any) => c.code === product.category_id || c.id === product.category_id)
      if (cat?.parent_id) {
        categoryLevel1.value = cat.parent_id
        categoryLevel2.value = cat.code || ''
      } else if (cat) {
        categoryLevel1.value = cat.code || ''
        categoryLevel2.value = ''
      } else {
        categoryLevel1.value = product.category_id
        categoryLevel2.value = ''
      }
    } else {
      categoryLevel1.value = ''
      categoryLevel2.value = ''
    }

    // 恢复供应商对象支持 SupplierSearchSelect 回填与检索
    if (form.supplier_name && !form.supplier) {
      try {
        const res = await suppliersApi.list({ skip: 0, limit: 20, keyword: form.supplier_name })
        const matched = (res.data || []).find((s: Supplier) => s.supplier_name?.trim() === form.supplier_name?.trim())
        if (matched) {
          form.supplier = matched
        } else {
          form.supplier = { id: 0, supplier_name: form.supplier_name } as Supplier
        }
      } catch {
        form.supplier = { id: 0, supplier_name: form.supplier_name } as Supplier
      }
    }

    await loadSupplierUrls()
  } else {
    // 新增模式：清空表单，并尝试使用传入的 customerId 或第一个客户
    assignForm(emptyForm())
    if (customerId) {
      form.customer_id = customerId
    } else if (customerOptions.value.length > 0) {
      form.customer_id = customerOptions.value[0].id
    }
    categoryLevel1.value = ''
    categoryLevel2.value = ''
    supplierUrlOptions.value = []
  }

  // 初始化初始数据快照，建立脏数据对比标准
  initialFormSnapshot.value = createFormSnapshot()
  visible.value = true
}

/**
 * 关闭对话框
 */
function close(): void {
  visible.value = false
}

/**
 * 校验并保存产品数据
 */
async function saveProduct(): Promise<void> {
  if (!formRef.value) return
  await formRef.value.validate()

  saving.value = true
  try {
    const payload: ProductFormPayload = {
      ...form,
      sub_images: form.extra_images,
      category_id: form.category_id || null,
      codes: editingProduct.value ? undefined : (form.factory_code ? splitList(form.factory_code) : undefined),
      oes: editingProduct.value ? undefined : (form.oe_number ? splitList(form.oe_number) : undefined)
    }

    if (editingProduct.value) {
      await productsApi.update(editingProduct.value.id, payload)
      ElMessage.success('产品已更新')
    } else {
      await productsApi.create(payload)
      ElMessage.success('产品已创建')
    }

    const currentProduct = editingProduct.value
    // 保存成功后更新快照，确保关闭不再误触未保存改动警告
    initialFormSnapshot.value = createFormSnapshot()
    close()
    emit('success', currentProduct)
  } catch (error) {
    console.error('[ProductManagementEditDialog] 保存产品失败:', error)
  } finally {
    saving.value = false
  }
}

/**
 * 对话框关闭回调
 */
function onClosed(): void {
  initialFormSnapshot.value = ''
  emit('closed')
}

defineExpose({
  open,
  close
})
</script>

<style scoped>
.product-management-edit-dialog {
  max-height: calc(88vh - 100px);
  overflow-y: auto;
  padding-right: 4px;
}

.product-management-edit-dialog::-webkit-scrollbar {
  width: 8px;
}
.product-management-edit-dialog::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
}
.product-management-edit-dialog::-webkit-scrollbar-track {
  background: #e2f0d9;
}

.edit-section {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 10px;
  overflow: hidden;
  background: #fff;
}

.section-title {
  padding: 7px 12px;
  font-weight: 600;
  font-size: 13px;
}

.section-body {
  padding: 10px 12px;
}

/* 1:1 复制 ProductEditDialog.vue CSS 样式 */
.basic-info-table {
  display: grid;
  grid-template-columns: 105px 1.25fr 105px 1.2fr 90px 1.05fr 105px 1.1fr 95px 1.1fr;
  grid-template-rows: 84px 48px 48px 72px;
  border: 1px solid #222;
  background: #fff;
  overflow: hidden;
}

.purchase-cost-table {
  display: grid;
  grid-template-columns: 105px 1fr 105px 1fr 105px 1fr 105px 1fr;
  grid-auto-rows: minmax(42px, auto);
  border: 1px solid #222;
  background: #fff;
  overflow: hidden;
}

.basic-info-label,
.basic-info-cell,
.basic-info-image,
.purchase-cost-head,
.purchase-cost-cell,
.sales-detail-head {
  min-width: 0;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  background: #fff;
  box-sizing: border-box;
}

.basic-info-label,
.purchase-cost-head,
.sales-detail-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #ff0000;
  font-size: 13px;
  line-height: 1.2;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.basic-info-label.required::before,
.purchase-cost-head.required::before,
.sales-detail-head.required::before {
  content: '*';
  margin-right: 3px;
  color: #ff0000;
}

.basic-info-label span {
  color: #c00000;
  font-size: 12px;
}

.basic-info-cell,
.basic-info-image,
.purchase-cost-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 6px;
}

.model-label { grid-column: 1; grid-row: 1; }
.model-cell { grid-column: 2 / 4; grid-row: 1; }

.emphasis-cell :deep(.el-input__inner),
.emphasis-cell :deep(.field-input .el-input__inner) {
  height: 76px;
  text-align: center;
  font-size: 25px !important;
  line-height: 76px;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.emphasis-cell :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f2f3f5;
  cursor: not-allowed;
}

.emphasis-cell :deep(.el-input.is-disabled .el-input__inner) {
  color: #606266;
  -webkit-text-fill-color: #606266;
}

.own-code-label { grid-column: 4; grid-row: 1; }
.own-code-cell {
  grid-column: 5 / 7;
  grid-row: 1;
  color: #f56c6c;
  font-family: 'Times New Roman', 'SimSun', serif;
  font-size: 13px;
}

.main-image-cell {
  grid-column: 7;
  grid-row: 1;
  padding: 4px;
  position: relative;
}

.extra-images-cell {
  grid-column: 8 / 11;
  grid-row: 1;
  padding: 4px 10px;
  justify-content: flex-start;
  border-right: none;
}

.pname-label { grid-column: 1; grid-row: 2 / 4; }
.product-name-zh { grid-column: 2 / 4; grid-row: 2; justify-content: flex-start; }
.product-name-en { grid-column: 2 / 4; grid-row: 3; justify-content: flex-start; }

.short-name-label { grid-column: 4; grid-row: 2 / 4; }
.short-name-zh { grid-column: 5 / 7; grid-row: 2; justify-content: flex-start; }
.short-name-en { grid-column: 5 / 7; grid-row: 3; justify-content: flex-start; }

.oe-label { grid-column: 7; grid-row: 2; }
.oe-cell { grid-column: 8 / 11; grid-row: 2; align-items: stretch; padding: 4px 8px; border-right: none; }

.remark-label { grid-column: 7; grid-row: 3; }
.remark-cell { grid-column: 8 / 11; grid-row: 3; align-items: stretch; padding: 4px 8px; border-right: none; }

.details-label { grid-column: 1; grid-row: 4; }
.details-cell { grid-column: 2 / 5; grid-row: 4; justify-content: flex-start; align-items: stretch; padding: 4px 8px; }

.color-label { grid-column: 5; grid-row: 4; }
.color-cell { grid-column: 6 / 8; grid-row: 4; justify-content: flex-start; }

.category-label { grid-column: 8; grid-row: 4; }
.category-cell { grid-column: 9 / 11; grid-row: 4; border-right: none; overflow: hidden; }

.category-select-group {
  display: flex;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

.category-select-group .el-select {
  flex: 1;
  min-width: 0;
}

.basic-info-table :deep(.el-input),
.basic-info-table :deep(.el-input-number),
.basic-info-table :deep(.field-input-wrapper),
.purchase-cost-table :deep(.el-input),
.purchase-cost-table :deep(.el-input-number),
.purchase-cost-table :deep(.field-input-wrapper) {
  width: 100%;
}

.image-uploader-main {
  width: 76px;
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.preview-image-main {
  width: 76px;
  height: 76px;
  object-fit: contain;
}

.extra-images-scroll {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  width: 100%;
  padding-bottom: 2px;
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
  width: 64px;
  height: 64px;
  border: none;
  border-radius: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: transparent;
  transition: color 0.2s;
}

.extra-image-uploader:hover {
  color: #409eff;
}

.extra-image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  height: 100%;
}

.extra-image-placeholder-text {
  color: #909399;
  font-size: 12px;
  line-height: 1;
}

.image-placeholder-icon {
  font-size: 20px;
  color: #909399;
}

.image-placeholder-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #c00000;
  font-size: 12px;
}

.main-image-required-star {
  position: absolute;
  top: 2px;
  right: 4px;
  color: #c00000;
  font-size: 16px;
  font-weight: bold;
  pointer-events: none;
  line-height: 1;
}

.pack-spec-popover {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px;
}

.pack-spec-locked {
  font-size: 13px;
  color: #606266;
}

.span-2 { grid-column: span 2; }
.span-3 { grid-column: span 3; }

.dialog-footer-content {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.table-form-item {
  margin-bottom: 0 !important;
  width: 100%;
}

.full-width {
  width: 100%;
}

/* ================= 参照图纸定制的 7 列 Excel 风格网格布局与视觉样式 ================= */
.purchase-cost-table-custom {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border: 1px solid #222;
  background: #fff;
  overflow: hidden;
}

.table-head,
.table-cell {
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  box-sizing: border-box;
  padding: 4px 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  line-height: 1.2;
}

.table-head {
  flex-direction: column;
  text-align: center;
  font-family: 'Times New Roman', 'SimSun', serif;
  font-weight: 500;
  color: #000;
  background: #fff;
}

/* 移除已有的 required::before 避免样式重叠冲突 */
.table-head.required::before {
  content: '';
}

/* --- 行 1 & 行 2 定位 (7 列布局) --- */
/* 报价 (PRICE/USD) - Col 1 */
.cell-quote-head {
  grid-column: 1;
  grid-row: 1;
  background-color: #f7c7a7 !important;
  color: #303133 !important;
  font-weight: 600;
}
.cell-quote-val {
  grid-column: 1;
  grid-row: 2;
  background-color: #f7c7a7 !important;
}

/* 人民币采购价 - Col 2 */
.cell-rmb-price-head {
  grid-column: 2;
  grid-row: 1;
  background-color: #f7c7a7 !important;
  color: #303133 !important;
  font-weight: 600;
}
.cell-rmb-price-val {
  grid-column: 2;
  grid-row: 2;
  background-color: #f7c7a7 !important;
}

/* 贴标费 - Col 3 */
.cell-labeling-head {
  grid-column: 3;
  grid-row: 1;
  background-color: #f7c7a7 !important;
  color: #303133 !important;
  font-weight: 600;
}
.cell-labeling-val {
  grid-column: 3;
  grid-row: 2;
  background-color: #f7c7a7 !important;
}

/* 运费 - Col 4 */
.cell-shipping-head {
  grid-column: 4;
  grid-row: 1;
  background-color: #f7c7a7 !important;
  color: #303133 !important;
  font-weight: 600;
}
.cell-shipping-val {
  grid-column: 4;
  grid-row: 2;
  background-color: #f7c7a7 !important;
}

/* 供应商 - Col 5 & 6 */
.cell-supplier-head { grid-column: 5; grid-row: 1; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-supplier-content { grid-column: 6; grid-row: 1; }

.cell-shop-url-head { grid-column: 5; grid-row: 2; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-shop-url-content { grid-column: 6; grid-row: 2; display: flex; align-items: center; gap: 4px; }

/* 开票情况 - Col 7 (就一列) */
.cell-invoice-group-head {
  grid-column: 7;
  grid-row: 1;
  background-color: #e2efda !important;
  color: #000 !important;
  font-weight: bold;
  font-size: 14px;
}
.cell-invoice-type { grid-column: 7; grid-row: 2; background-color: #e2efda !important; }

/* --- 行 3a & 3b (中间块 2 子行高度) --- */
/* 产品特性/选项/采购备注 - Col 1 (头), Col 2-3 (内容跨 2 列) */
.cell-product-detail-head { grid-column: 1; grid-row: 3 / 5; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-product-detail-content { grid-column: 2 / 4; grid-row: 3 / 5; justify-content: stretch; align-items: stretch; }

/* 采购方式 & 开票工厂 (Row 3 / 行 3a: Col 4 头, Col 5 值; Col 6 头, Col 7 值) */
.cell-purchase-option-head { grid-column: 4; grid-row: 3; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-purchase-option-content { grid-column: 5; grid-row: 3; }

.cell-factory-invoice-head { grid-column: 6; grid-row: 3; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-factory-invoice-content { grid-column: 7; grid-row: 3; }

/* 付款方式 & 货源地 (Row 4 / 行 3b: Col 4 头, Col 5 值; Col 6 头, Col 7 值) */
.cell-payment-method-head { grid-column: 4; grid-row: 4; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-payment-method-content { grid-column: 5; grid-row: 4; }

.cell-source-place-head { grid-column: 6; grid-row: 4; background-color: #e2efda !important; color: #000 !important; font-weight: bold; }
.cell-source-place-content { grid-column: 7; grid-row: 4; }

/* --- 行 5 & 行 6 (纸箱包装与规格，全行背景同步为灰底 #d9d9d9) --- */
.cell-carton-pack-head { grid-column: 1 / 4; grid-row: 5; background-color: #d9d9d9 !important; font-weight: bold; }
.cell-pack-spec-head { grid-column: 4; grid-row: 5; background-color: #d9d9d9 !important; font-weight: bold; }
.cell-carton-gross-weight-head { grid-column: 5; grid-row: 5; background-color: #d9d9d9 !important; font-weight: bold; }
.cell-estimated-volume-head { grid-column: 6; grid-row: 5; background-color: #d9d9d9 !important; font-weight: bold; }
.cell-estimated-gross-weight-head { grid-column: 7; grid-row: 5; background-color: #d9d9d9 !important; font-weight: bold; }

.cell-carton-length { grid-column: 1; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-carton-width { grid-column: 2; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-carton-height { grid-column: 3; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-pack-spec-content { grid-column: 4; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-carton-gross-weight-content { grid-column: 5; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-estimated-volume-content { grid-column: 6; grid-row: 6; background-color: #d9d9d9 !important; }
.cell-estimated-gross-weight-content { grid-column: 7; grid-row: 6; background-color: #d9d9d9 !important; }

/* ================= 表格体无缝输入框与选中高亮样式 ================= */

/* 1. 消除 Element Plus 表格内嵌套输入框与下拉选的白边框、投影与背景，使单元格本身充当输入框 */
.cell-supplier-content {
  padding: 0;
  width: 100%;
}

.cell-supplier-content :deep(.el-select),
.cell-supplier-content :deep(.supplier-search-select) {
  width: 100%;
}

.basic-info-table :deep(.el-input__wrapper),
.basic-info-table :deep(.el-select__wrapper),
.basic-info-table :deep(.el-textarea__inner),
.basic-info-table :deep(.field-input-wrapper),
.purchase-cost-table-custom :deep(.el-input__wrapper),
.purchase-cost-table-custom :deep(.el-select__wrapper),
.purchase-cost-table-custom :deep(.el-textarea__inner),
.purchase-cost-table-custom :deep(.field-input-wrapper),
.table-cell :deep(.el-input__wrapper),
.table-cell :deep(.el-select__wrapper),
.table-cell :deep(.el-textarea__inner),
.table-cell :deep(.field-input-wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0 4px;
  background: transparent;
  width: 100%;
}

.basic-info-table :deep(.el-input__inner),
.purchase-cost-table-custom :deep(.el-input__inner),
.table-cell :deep(.el-input__inner),
.table-cell :deep(.el-select__selected-item),
.table-cell :deep(.el-select__placeholder),
.table-cell :deep(.el-input__prefix) {
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
  text-align: center;
  color: #000;
}

/* 2. 隐藏数字输入框控制按钮，保持单元格排版整洁无缝 */
.purchase-cost-table-custom :deep(.el-input-number .el-input-number__decrease),
.purchase-cost-table-custom :deep(.el-input-number .el-input-number__increase) {
  display: none;
}
.purchase-cost-table-custom :deep(.el-input-number .el-input__wrapper) {
  padding: 0 4px !important;
}

/* 3. 焦点激活高亮效果：当前选中的输入框与下拉选择框呈现柔和黄底与橙黄立体边框 */
.basic-info-cell :deep(.el-input__wrapper:focus-within),
.basic-info-cell :deep(.el-select__wrapper:focus-within),
.basic-info-cell :deep(.el-textarea__inner:focus-within),
.table-cell :deep(.el-input__wrapper:focus-within),
.table-cell :deep(.el-select__wrapper:focus-within),
.table-cell :deep(.el-textarea__inner:focus-within) {
  background-color: #fffbe6 !important;
  outline: 2px solid #e6a23c !important;
  border-radius: 3px;
}
</style>
