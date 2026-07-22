<template>
  <el-dialog
    v-model="visible"
    :title="`采购订单 (${items.length} 个产品)`"
    width="1100px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <!-- 产品信息表格（放在采购 Tabs 之前） -->
    <div class="product-table-section">
      <div class="section-title">产品信息 ({{ items.length }} 个)</div>
      <el-table :data="items" border size="small" max-height="300">
        <el-table-column prop="product_name" label="产品名称" width="140" />
        <el-table-column prop="customer_model" label="型号" width="110" />
        <el-table-column prop="quantity" label="数量" width="60" align="right" />
        <el-table-column label="商品单价" width="100">
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.unit_price"
              :min="0"
              :precision="2"
              size="small"
              @change="recalcTotal($index)"
            />
          </template>
        </el-table-column>
        <el-table-column label="贴标费" width="90">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.labeling_fee" :min="0" :precision="2" size="small" @change="recalcTotal($index)" />
          </template>
        </el-table-column>
        <el-table-column label="税费" width="90">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.tax_fee" :min="0" :precision="2" size="small" @change="recalcTotal($index)" />
          </template>
        </el-table-column>
        <el-table-column label="运费" width="90">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.shipping_fee" :min="0" :precision="2" size="small" @change="recalcTotal($index)" />
          </template>
        </el-table-column>
        <el-table-column label="1688链接" width="220">
          <template #default="{ row, $index }">
            <el-select
              v-model="row.link"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入链接"
              size="small"
              @change="(url: string) => onItemUrlChange($index, url)"
            >
              <el-option
                v-for="u in (row._urlOptions || [])"
                :key="u.id || u.url"
                :label="u.display_name || u.url"
                :value="u.url"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="总金额" width="120">
          <template #default="{ row }">
            <span class="total-amount">{{ formatMoney(row._total || 0) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-tabs v-model="purchaseType" class="purchase-tabs">
      <!-- 线上采购 Tab -->
      <el-tab-pane label="线上采购" name="online">
        <el-form label-width="120px" class="online-form">
          <!-- 平台选择 -->
          <div class="platform-section">
            <el-radio-group v-model="platform" @change="onPlatformChange">
              <el-radio value="1688">1688</el-radio>
              <el-radio value="wechat">微信</el-radio>
            </el-radio-group>
          </div>

          <!-- 1688 采购表单 -->
          <template v-if="platform === '1688'">
            <el-form-item label="1688店铺名称 *" required>
              <el-input v-model="autoFillShopName" placeholder="请输入1688店铺名称" />
            </el-form-item>
            <el-form-item label="1688链接">
              <el-input v-model="linkUrl" placeholder="https://detail.1688.com/..." />
            </el-form-item>
            <el-form-item label="微信联系方式">
              <el-input v-model="contactWechat" placeholder="可选，其他联系方式" />
            </el-form-item>
            <el-form-item label="采购凭证">
              <el-input v-model="screenshotPath" placeholder="凭证文件路径（可选）" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="onlineRemark" type="textarea" :rows="2" placeholder="可选填写备注" />
            </el-form-item>
          </template>

          <!-- 微信采购表单 -->
          <template v-else>
            <el-form-item label="微信号 *" required>
              <el-input v-model="wechatId" placeholder="卖家微信号" />
            </el-form-item>
            <el-form-item label="微信昵称 *" required>
              <el-input v-model="wechatNickname" placeholder="卖家微信昵称" />
            </el-form-item>
            <el-form-item label="1688链接">
              <el-input v-model="linkUrl" placeholder="可选，关联的1688链接" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="onlineRemark" type="textarea" :rows="2" placeholder="可选填写备注" />
            </el-form-item>
          </template>
        </el-form>
      </el-tab-pane>

      <!-- 线下采购 Tab -->
      <el-tab-pane label="线下采购" name="offline">
        <el-form label-width="120px" class="offline-form">
          <el-form-item label="合同选项">
            <el-checkbox v-model="generateContract">生成采购合同</el-checkbox>
          </el-form-item>
          <el-form-item label="供应商">
            <div class="supplier-select-row">
              <el-select
                v-model="selectedSupplierId"
                placeholder="搜索供应商名称/编号/联系人"
                class="supplier-select"
                filterable
                remote
                :remote-method="searchSuppliers"
                :loading="supplierLoading"
                clearable
                @change="onSupplierChange"
                popper-class="supplier-select-popper"
              >
                <el-option label="-- 请选择 --" :value="null" />
                <el-option
                  v-for="s in suppliers"
                  :key="s.id"
                  :label="`${s.supplier_code ? s.supplier_code + ' - ' : ''}${s.supplier_name}${s.contact_person ? ' (' + s.contact_person + ')' : ''}`"
                  :value="s.id"
                />
                <template #empty>
                  <div class="supplier-empty">
                    <span>未找到供应商</span>
                  </div>
                </template>
                <template #footer>
                  <div class="supplier-footer" @click="openCreateSupplierDialog">
                    <el-icon><Plus /></el-icon>
                    <span>新建供应商「{{ lastSupplierQuery || '' }}」</span>
                  </div>
                </template>
              </el-select>
              <el-button type="primary" plain @click="openCreateSupplierDialog">
                <el-icon><Plus /></el-icon>
                添加供应商
              </el-button>
            </div>
          </el-form-item>
          <el-form-item label="联系人">
            <el-input v-model="supplierContact" placeholder="供应商联系人" />
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="supplierPhone" placeholder="供应商联系电话" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="offlineRemark" type="textarea" :rows="2" placeholder="可选填写备注" />
          </el-form-item>
          <el-form-item label="合同备注">
            <el-input v-model="contractRemark" type="textarea" :rows="2" placeholder="合同特殊条款" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 发票信息 -->
    <div class="invoice-section">
      <div class="section-title">发票信息</div>
      <el-form label-width="100px" inline>
        <el-form-item label="发票金额">
          <el-input-number v-model="invoiceAmount" :min="0" :precision="2" size="small" />
        </el-form-item>
        <el-form-item label="币种">
          <el-select v-model="invoiceCurrency" size="small" style="width: 100px">
            <el-option label="CNY" value="CNY" />
            <el-option label="USD" value="USD" />
            <el-option label="EUR" value="EUR" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="onClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">确认采购</el-button>
    </template>
  </el-dialog>

  <!-- 新建供应商（复用 SupplierFormDialog） -->
  <SupplierFormDialog
    v-model="createSupplierDialogVisible"
    :supplier="null"
    :default-platform="purchaseType === 'offline' ? 'offline' : platform"
    @success="onSupplierCreated"
  />
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { purchaseApi, type PurchasePayload, type PurchaseItem, createOnlinePurchase, type PurchaseCreateOnline } from '@/api/purchase'
import { apiUrl } from '@/api/base'
import { SUPPLIERS } from '@/api/endpoints'
import { pendingSupplierState } from '@/api/suppliers'
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'
import SupplierFormDialog from '@/components/supplier/SupplierFormDialog.vue'
import type { Supplier } from '@/api/suppliers'
import type { OrderDetailItem } from '@/types/orderSummary'

const emit = defineEmits<{
  success: [],
  'purchase-complete': [payload: {
    factory_name: string
    shop_url: string
    wechatId: string
    wechatNickname: string
  }]
}>()

const visible = ref(false)
const submitting = ref(false)
const items = ref<OrderDetailItem[]>([])

// 采购类型
const purchaseType = ref<'online' | 'offline'>('online')
const platform = ref<'1688' | 'wechat' | 'offline'>('1688')

// 币种

// 1688采购
const shopName = ref('')
const autoFillShopName = ref('')  // 保存从供应商/prefill自动填入的店铺名，tab切换时不丢失
const linkUrl = ref('')
const contactWechat = ref('')
const screenshotPath = ref('')
const onlineRemark = ref('')

// 微信采购
const wechatId = ref('')
const wechatNickname = ref('')

// 线下采购
const suppliers = ref<any[]>([])
const suppliersCache = ref<any[]>([])  // 缓存全量供应商，用于本地搜索
const supplierLoading = ref(false)
const lastSupplierQuery = ref('')        // 最近一次搜索词
const selectedSupplierId = ref<number | null>(null)
const supplierContact = ref('')
const supplierPhone = ref('')
const offlineRemark = ref('')
const contractRemark = ref('')
const generateContract = ref(true)

// 新建供应商（复用 SupplierFormDialog）
const createSupplierDialogVisible = ref(false)

// 发票
const invoiceAmount = ref(0)
const invoiceCurrency = ref('CNY')

let orderId: number | null = null
let prefillUrls: Record<number, string[]> = {}

async function open(
  orderItems: OrderDetailItem[],
  piId: number,
  urls: Record<number, string[]> = {},
  prefillShopName: string = '',
  prefillLinkUrl: string = ''
) {
  visible.value = true
  orderId = piId
  prefillUrls = urls

  // 在异步加载供应商列表前快照 ProductEditDialog 传来的供应商，
  // 避免等待期间共享状态被其他流程清空，导致 1688 店铺名称丢失。
  const pending = {
    supplier: pendingSupplierState.supplier,
    platform: pendingSupplierState.platform,
    shop_link: pendingSupplierState.shop_link,
    wechat_id: pendingSupplierState.wechat_id,
    wechat_nickname: pendingSupplierState.wechat_nickname,
  }

  // 初始化产品数据
  items.value = orderItems.map((item) => ({
    ...item,
    unit_price: item.purchase_price ?? 0,
    // ProductEditDialog 的 misc_fee 是贴标费、税费和运费的汇总。
    // 没有历史 1688 明细时，先将已有杂费放入贴标费列，避免费用丢失。
    labeling_fee: item.labeling_fee ?? item.misc_fee ?? 0,
    tax_fee: item.tax_fee ?? 0,
    shipping_fee: item.shipping_fee ?? 0,
    freight: 0,
    link: urls[item.product_id!]?.[0] || '',
    _urlOptions: urls[item.product_id!] || [],
    _total: 0,
  }))
  items.value.forEach((_, index) => recalcTotal(index))

  // 加载初始费用
  loadInitialPrices()

  // 重置表单（purchaseType 默认为 'online'，platform 默认为 '1688'）
  resetForm()

  // 加载供应商列表（需等待完成才能匹配供应商）
  await loadSuppliers()

  // 顶层 1688 店铺名称预填（来自 order 或产品的供应商名，独立于 pendingSupplierState）
  if (prefillShopName) {
    shopName.value = prefillShopName
    autoFillShopName.value = prefillShopName
  }
  // 顶层采购链接预填
  if (prefillLinkUrl) {
    linkUrl.value = prefillLinkUrl
  }

  // ProductEditDialog 选择/新建供应商后，自动回填采购表单
  if (pending.supplier) {
    const supplierPlatform = pending.platform || '1688'
    
    if (supplierPlatform === 'offline') {
      // 线下采购：切换 Tab 并匹配供应商下拉
      purchaseType.value = 'offline'
      const found = suppliersCache.value.find((s: any) => s.id === pending.supplier!.id)
      if (found) {
        selectedSupplierId.value = found.id
        onSupplierChange(found.id)
      }
    } else {
      // 线上采购：切换 Tab 并填入对应平台字段
      purchaseType.value = 'online'
      platform.value = supplierPlatform
      
      if (supplierPlatform === '1688') {
        const name = pending.supplier!.supplier_name || ''
        shopName.value = name
        autoFillShopName.value = name
        if (pending.shop_link) {
          linkUrl.value = pending.shop_link
        }
        if (pending.wechat_id) {
          contactWechat.value = pending.wechat_id
        }
        // 加载所有产品行的 URL 历史下拉
        await reloadAllUrls()
      } else if (supplierPlatform === 'wechat') {
        // 微信供应商：回填微信号和昵称，不填 1688 店铺名称。
        wechatId.value = pending.wechat_id || pending.supplier!.wechat_id || pending.supplier!.supplier_name || ''
        wechatNickname.value = pending.wechat_nickname || pending.supplier!.wechat_nickname || ''
      }
    }
    
    // 清空共享状态（只消费一次）
    pendingSupplierState.supplier = null
    pendingSupplierState.platform = '1688'
    pendingSupplierState.shop_link = null
    pendingSupplierState.wechat_id = null
    pendingSupplierState.wechat_nickname = null
  }
}

// 加载供应商列表（一次性加载全量，本地搜索）
async function loadSuppliers() {
  supplierLoading.value = true
  try {
    const res = await fetch(apiUrl(SUPPLIERS.list))
    if (res.ok) {
      const data = (await res.json()) || []
      suppliers.value = data
      suppliersCache.value = data
    }
  } catch (e) {
    console.warn('加载供应商失败', e)
  } finally {
    supplierLoading.value = false
  }
}

// 远程搜索供应商（本地过滤，避免每次请求后端）
function searchSuppliers(query: string) {
  lastSupplierQuery.value = query || ''
  if (!query) {
    suppliers.value = suppliersCache.value
    return
  }
  const q = query.toLowerCase().trim()
  suppliers.value = suppliersCache.value.filter(
    (s: any) =>
      (s.supplier_name || '').toLowerCase().includes(q) ||
      (s.supplier_code || '').toLowerCase().includes(q) ||
      (s.contact_person || '').toLowerCase().includes(q) ||
      (s.phone || '').toLowerCase().includes(q)
  )
}

// 选中供应商后自动填充联系人/电话
function onSupplierChange(val: number | null) {
  if (!val) {
    return
  }
  const supplier = suppliersCache.value.find((s: any) => s.id === val)
  if (supplier) {
    supplierContact.value = supplier.contact_person || supplierContact.value
    supplierPhone.value = supplier.phone || supplierPhone.value
  }
}

// 打开新建供应商对话框
function openCreateSupplierDialog() {
  createSupplierDialogVisible.value = true
}

// SupplierFormDialog 创建成功回调
function onSupplierCreated(created: Supplier) {
  // 添加到本地缓存
  suppliersCache.value.push(created)
  suppliers.value = [...suppliersCache.value]
  
  if (purchaseType.value === 'offline') {
    // 线下采购：匹配供应商下拉
    selectedSupplierId.value = created.id
    onSupplierChange(created.id)
  } else {
    // 线上采购（1688/微信）：1688 平台时把店铺名填入 autoFillShopName
    if (platform.value === '1688') {
      autoFillShopName.value = created.supplier_name || ''
      shopName.value = created.supplier_name || ''
      if (created.shop_link) {
        linkUrl.value = created.shop_link
      }
    }
  }
  createSupplierDialogVisible.value = false
}

function resetForm() {
  purchaseType.value = 'online'
  platform.value = '1688'
  // shopName / linkUrl 由 autoFillShopName 保存，不清空以便 tab 切换后恢复
  contactWechat.value = ''
  screenshotPath.value = ''
  onlineRemark.value = ''
  wechatId.value = ''
  wechatNickname.value = ''
  selectedSupplierId.value = null
  supplierContact.value = ''
  supplierPhone.value = ''
  offlineRemark.value = ''
  contractRemark.value = ''
  generateContract.value = true
  invoiceAmount.value = 0
  invoiceCurrency.value = 'CNY'
}

// URL 选项携带接口（用于扩展 row._urlOptions 类型）
interface UrlOptionCarrier {
  _urlOptions?: ProductSupplierUrl[]
}

// 重新加载所有行的 URL 历史下拉选项
async function reloadAllUrls() {
  const supplier = pendingSupplierState.supplier
  if (!supplier) return
  for (const row of items.value as any[]) {
    if (!row.product_id) continue
    try {
      const res = await productSupplierUrlsApi.list(row.product_id, supplier.id, supplier.supplier_name)
      row._urlOptions = res || []
    } catch (e) { row._urlOptions = [] }
  }
}

// 行 URL 变更处理（URL 历史由后端事务写入，前端只更新 row.link）
function onItemUrlChange(index: number, url: string) {
  ;(items.value[index] as any).link = url
}

// 加载初始费用（从最近采购记录 + 历史 1688 链接）
async function loadInitialPrices() {
  for (let i = 0; i < items.value.length; i++) {
    const item = items.value[i]
    if (!item.product_id) continue

    // 1) 并行加载最近采购记录与历史链接列表
    const [latestRes, urlsRes] = await Promise.allSettled([
      purchaseApi.getProductLatestPurchase(item.product_id),
      purchaseApi.getRecent1688Urls(item.product_id, 5),
    ])

    // 1.1) 最近采购记录（采购价/费用/链接兜底）
    if (latestRes.status === 'fulfilled') {
      const res = latestRes.value
      // 兼容后端当前 { success, record } 与旧版 { code, data: { record } } 响应。
      const payload = res.data as typeof res.data & { record?: any }
      const record = payload.record ?? payload.data?.record
      if ((payload.success === true || payload.code === 200) && record) {
        item.unit_price = record.unit_price ?? item.purchase_price ?? 0
        item.labeling_fee = record.labeling_fee ?? 0
        item.tax_fee = record.tax_fee ?? 0
        item.shipping_fee = record.shipping_fee ?? record.freight ?? 0
        item.freight = 0
        // 历史供应商名称 → 1688 店铺名称（如果当前为空）
        if (record.supplier_name && !autoFillShopName.value) {
          autoFillShopName.value = record.supplier_name
          shopName.value = record.supplier_name
        }
        if (!item.link && record.link) {
          item.link = record.link
        }
        recalcTotal(i)
      }
    } else {
      console.warn('加载采购记录失败', latestRes.reason)
    }

    // 1.2) 历史 1688 链接下拉选项（去重，包含当前链接）
    const urlOptions: string[] = []
    if (urlsRes.status === 'fulfilled') {
      const res = urlsRes.value
      if (res.data.code === 200 && Array.isArray(res.data.data?.urls)) {
        urlOptions.push(...res.data.data.urls)
      }
    } else {
      console.warn('加载历史1688链接失败', urlsRes.reason)
    }
    // 把当前链接也加入选项（如果不在列表里）
    if (item.link && !urlOptions.includes(item.link)) {
      urlOptions.unshift(item.link)
    }
    ;(item as any)._urlOptions = urlOptions.slice(0, 10)
  }
}

// 1688 链接变更：同步到 pi_item.shop_url
async function onLinkChange(index: number, val: string) {
  const item = items.value[index]
  if (!item) return
  // 仅当有 pi_item_id 时同步到后端
  if (!item.id) {
    console.warn('[PurchaseDialog] 该产品行无 pi_item_id，跳过链接同步')
    return
  }
  try {
    await purchaseApi.updatePiItemLink(item.id, val || '')
    console.log(`[PurchaseDialog] 已同步 1688 链接到 pi_item ${item.id}: ${val}`)
  } catch (e) {
    console.warn('[PurchaseDialog] 同步 1688 链接失败', e)
  }
}

function recalcTotal(index: number) {
  const item = items.value[index]
  if (!item) return
  item._total =
    (item.unit_price || 0) * (item.quantity || 0) +
    (item.labeling_fee || 0) +
    (item.tax_fee || 0) +
    (item.shipping_fee || 0)
}

function formatMoney(amount: number): string {
  return amount.toFixed(2) + ' RMB'
}

function onPlatformChange() {
  // 切换平台时只清空当前平台的特有字段，shopName 为线上采购通用字段应保留
  linkUrl.value = ''
  contactWechat.value = ''
}

function onClose() {
  visible.value = false
  items.value = []
}

async function onSubmit() {
  // 校验
  if (!orderId) {
    ElMessage.warning('缺少订单信息')
    return
  }

  if (purchaseType.value === 'online' && platform.value === '1688') {
    if (!autoFillShopName.value.trim()) {
      ElMessage.warning('请输入1688店铺名称')
      return
    }
  }

  if (purchaseType.value === 'online' && platform.value === 'wechat') {
    if (!wechatNickname.value.trim()) {
      ElMessage.warning('请输入微信昵称')
      return
    }
  }

  if (purchaseType.value === 'offline' && !selectedSupplierId.value) {
    ElMessage.warning('请选择供应商')
    return
  }

  try {
    submitting.value = true

    const payload: PurchasePayload = {
      dept_id: 'S',
      pi_id: orderId!,
      items: items.value.map((item) => ({
        product_id: item.product_id!,
        pi_item_id: item.id,
        supplier_id: item.supplier_id,
        product_name: item.product_name,
        customer_model: item.customer_model || undefined,
        factory_code: item.factory_code || undefined,
        product_image: item.image_url || undefined,
        color: item.product_feature || undefined,
        detail_requirement: item.remark || undefined,
        link: item.link,
        quantity: item.quantity,
        unit_price: item.unit_price || 0,
        labeling_fee: item.labeling_fee || 0,
        tax_fee: item.tax_fee || 0,
        shipping_fee: item.shipping_fee || 0,
        remark: '',
      })),
    }

    if (purchaseType.value === 'online') {
      // 新逻辑：直接传 platform + supplier_name，后端自动 find-or-create
      const onlinePayload: PurchaseCreateOnline = {
        dept_id: 'S',
        pi_id: orderId!,
        platform: platform.value,
        items: payload.items,
        supplier_name: platform.value === '1688' ? autoFillShopName.value : wechatNickname.value,
        shop_link: platform.value === '1688' ? (linkUrl.value || null) : null,
        link: linkUrl.value || null,
        contact_wechat: platform.value === '1688' ? contactWechat.value : wechatId.value,
        screenshot: screenshotPath.value || null,
        remark: onlineRemark.value || null,
        wechat_id: platform.value === 'wechat' ? (wechatId.value || null) : null,
        wechat_nickname: platform.value === 'wechat' ? (wechatNickname.value || null) : null,
        is_dropship: false,
        supplier_contact: null,
        supplier_phone: null,
      }
      const result = await createOnlinePurchase(onlinePayload)
      if (result.success) {
        ElMessage.success('采购订单创建成功')
        emit('success')
        emit('purchase-complete', {
          factory_name: platform.value === 'wechat'
            ? `${wechatNickname.value}(微信: ${wechatId.value})`
            : autoFillShopName.value,
          shop_url: linkUrl.value,
          wechatId: platform.value === 'wechat' ? wechatId.value : '',
          wechatNickname: platform.value === 'wechat' ? wechatNickname.value : '',
        })
        onClose()
      } else {
        ElMessage.error('采购失败')
      }
    } else {
      payload.supplier_id = selectedSupplierId.value!
      payload.generate_contract = generateContract.value
      payload.supplier_contact = supplierContact.value
      payload.supplier_phone = supplierPhone.value
      payload.remark = offlineRemark.value
      payload.contract_remark = contractRemark.value
      const res = await purchaseApi.createOfflinePurchase(payload)
      if (res.data.code === 200) {
        ElMessage.success('采购订单创建成功')
        emit('success')
        emit('purchase-complete', {
          factory_name: platform.value === 'wechat'
            ? `${wechatNickname.value}(微信: ${wechatId.value})`
            : autoFillShopName.value,
          shop_url: linkUrl.value,
          wechatId: platform.value === 'wechat' ? wechatId.value : '',
          wechatNickname: platform.value === 'wechat' ? wechatNickname.value : '',
        })
        onClose()
      } else {
        ElMessage.error(res.data.message || '采购失败')
      }
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '采购失败')
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.supplier-empty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  color: #909399;
}

.supplier-select-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.supplier-select {
  flex: 1;
  min-width: 0;
}

.supplier-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-top: 4px;
  border-top: 1px solid #ebeef5;
  color: #409eff;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s;
}

.supplier-footer:hover {
  background-color: #ecf5ff;
}

.purchase-tabs {
  margin-bottom: 16px;
}

.platform-section {
  margin-bottom: 16px;
}

.product-table-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #2563eb;
}

.total-amount {
  font-weight: 600;
  color: #2563eb;
  white-space: pre-line;
}

.invoice-section {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}
</style>
