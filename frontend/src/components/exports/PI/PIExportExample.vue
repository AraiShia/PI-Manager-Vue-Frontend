<template>
  <div class="pi-export-container">
    <!-- 顶部操作控制栏 -->
    <div class="action-bar no-print">
      <div class="action-bar-left">
        <h3 class="action-title">PI 导出版头原型预览 (Proforma Invoice Header Prototype)</h3>
        <el-tag type="info" effect="plain">单据编号: {{ piData.pi_no }}</el-tag>
      </div>
      <div class="action-bar-right">
        <el-switch
          v-model="isEditMode"
          active-text="实时编辑"
          inactive-text="预览排版"
          style="margin-right: 12px"
        />
        <el-button type="primary" plain :icon="Printer" @click="handlePrint">
          打印 / 另存为 PDF
        </el-button>
        <el-button type="success" :icon="Download" @click="handleExportExcel">
          导出 Excel
        </el-button>
      </div>
    </div>

    <!-- PI 表格渲染区域（完全对齐 Excel 表头结构） -->
    <div ref="exportTargetRef" class="pi-sheet-wrapper">
      <div class="pi-sheet">
        <!-- 1. 公司英文大标题 (HANGZHOU WEINA TRADE CO., LTD.) -->
        <div class="company-header-title">
          {{ piData.company_name }}
        </div>

        <!-- 2. PI 编号与下单日期行 -->
        <div class="pi-meta-row">
          <div class="meta-item left">
            <span class="meta-label">PI. NO. :</span>
            <input
              v-if="isEditMode"
              v-model="piData.pi_no"
              class="inline-input"
            />
            <span v-else class="meta-value">{{ piData.pi_no }}</span>
          </div>
          <div class="meta-item right">
            <span class="meta-label">Order Date:</span>
            <input
              v-if="isEditMode"
              v-model="piData.order_date"
              class="inline-input"
            />
            <span v-else class="meta-value">{{ formatDateOnly(piData.order_date) }}</span>
            <span class="meta-hint">(生产正式合同的日期)</span>
          </div>
        </div>

        <!-- 3. PROFORMA INVOICE 居中主标题 -->
        <div class="pi-main-title">
          PROFORMA INVOICE
        </div>

        <!-- 4. 买方与卖方双栏表格 (BUYER vs SELLER) -->
        <table class="pi-info-table">
          <thead>
            <tr>
              <th colspan="2" class="section-head buyer-head">BUYER (买方信息)</th>
              <th colspan="2" class="section-head seller-head">SELLER:（卖方信息）</th>
            </tr>
          </thead>
          <tbody>
            <!-- 第 1 行：TO vs Contact -->
            <tr>
              <td class="label-col">TO:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.buyer.name" class="inline-input" />
                <span v-else>{{ piData.buyer.name }}</span>
              </td>
              <td class="label-col">Contact:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.seller.contact" class="inline-input" />
                <span v-else>{{ piData.seller.contact }}</span>
              </td>
            </tr>

            <!-- 第 2 行：Tel vs Tel/WhatsApp -->
            <tr>
              <td class="label-col">Tel:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.buyer.tel" class="inline-input" />
                <span v-else>{{ piData.buyer.tel }}</span>
              </td>
              <td class="label-col">Tel/WhatsApp:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.seller.tel_whatsapp" class="inline-input" />
                <span v-else>{{ piData.seller.tel_whatsapp }}</span>
              </td>
            </tr>

            <!-- 第 3 行：ADDRESS vs ADDRESS (多行文本) -->
            <tr>
              <td class="label-col align-top">ADDRESS:</td>
              <td class="content-col multiline">
                <textarea v-if="isEditMode" v-model="piData.buyer.address" class="inline-textarea" rows="3" />
                <div v-else class="multiline-text">{{ piData.buyer.address }}</div>
              </td>
              <td class="label-col align-top">ADDRESS:</td>
              <td class="content-col multiline">
                <textarea v-if="isEditMode" v-model="piData.seller.address" class="inline-textarea" rows="4" />
                <div v-else class="multiline-text">{{ piData.seller.address }}</div>
              </td>
            </tr>

            <!-- 第 4 行：Final Destination vs Delivery date -->
            <tr>
              <td class="label-col">Final Destination:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.buyer.final_destination" class="inline-input" />
                <span v-else>{{ piData.buyer.final_destination }}</span>
              </td>
              <td class="label-col">Delivery date:</td>
              <td class="content-col">
                <input v-if="isEditMode" v-model="piData.seller.delivery_date" class="inline-input" />
                <span v-else>{{ piData.seller.delivery_date }}</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 5. 示例产品明细表格 (完全匹配 10 列表头结构) -->
        <table class="pi-items-table">
          <thead>
            <tr>
              <th style="width: 100px">NAME</th>
              <th style="width: 90px">CODE</th>
              <th style="width: 60px">PHOTO</th>
              <th>Description</th>
              <th style="width: 110px">Specification</th>
              <th style="width: 70px">pcs/ctn</th>
              <th style="width: 70px">Color</th>
              <th style="width: 60px">QTY</th>
              <th style="width: 85px">PRICE FOB</th>
              <th style="width: 95px">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in piData.items" :key="index">
              <td>
                <input v-if="isEditMode" v-model="item.name" class="inline-input" />
                <span v-else>{{ item.name }}</span>
              </td>
              <td class="text-center">
                <input v-if="isEditMode" v-model="item.code" class="inline-input" />
                <span v-else>{{ item.code }}</span>
              </td>
              <td class="text-center">
                <div v-if="item.no_knife_icon" class="no-knife-icon" title="No crossed knife">
                  <span class="cross-line"></span>
                  🔪
                </div>
                <div v-else class="photo-placeholder">PHOTO</div>
              </td>
              <td>
                <input v-if="isEditMode" v-model="item.description" class="inline-input" />
                <span v-else>{{ item.description }}</span>
              </td>
              <td class="text-center">
                <input v-if="isEditMode" v-model="item.specification" class="inline-input" />
                <span v-else>{{ item.specification }}</span>
              </td>
              <td class="text-center">
                <input v-if="isEditMode" v-model="item.pcs_ctn" class="inline-input" />
                <span v-else>{{ item.pcs_ctn }}</span>
              </td>
              <td class="text-center">
                <input v-if="isEditMode" v-model="item.color" class="inline-input" />
                <span v-else>{{ item.color }}</span>
              </td>
              <td class="text-right">
                <input v-if="isEditMode" v-model.number="item.qty" type="number" class="inline-input text-right" />
                <span v-else>{{ item.qty }}</span>
              </td>
              <td class="text-right">
                <input v-if="isEditMode" v-model.number="item.unit_price" type="number" class="inline-input text-right" />
                <span v-else>${{ item.unit_price.toFixed(2) }}</span>
              </td>
              <td
                class="text-right font-bold"
                :class="{ 'text-red': item.amount_override === 0 }"
              >
                ${{ getItemAmount(item).toFixed(2) }}
              </td>
            </tr>

            <!-- 附加优惠/加费用 (Additional benefits) 行：描述列占 8 列，金额列跨 2 列 -->
            <tr v-if="piData.additional_benefits" class="additional-benefits-row">
              <td colspan="8" class="text-left font-bold">
                <input v-if="isEditMode" v-model="piData.additional_benefits.label" class="inline-input text-left" />
                <span v-else>{{ piData.additional_benefits.label }}</span>
              </td>
              <td colspan="2" class="text-right font-bold text-red yellow-bg">
                <input v-if="isEditMode" v-model.number="piData.additional_benefits.amount" type="number" class="inline-input text-right text-red" />
                <span v-else>${{ piData.additional_benefits.amount.toFixed(2) }}</span>
              </td>
            </tr>
          </tbody>

          <!-- 汇总 TOTAL 行 -->
          <tfoot>
            <tr class="total-summary-row">
              <td colspan="7" class="text-left font-bold total-title-col">
                TOTAL :
              </td>
              <td class="text-center font-bold total-qty-col">
                {{ totalQuantity }}
              </td>
              <td colspan="2" class="text-left font-bold total-amount-col">
                ${{ formatMoney(totalAmount) }}
              </td>
            </tr>
          </tfoot>
        </table>

        <!-- 6. SAY TOTAL 行 (英文金额大写) -->
        <div class="say-total-row">
          <span class="say-total-label">SAY TOTAL:</span>
          <span class="say-total-value">{{ sayTotalText }}</span>
        </div>

        <!-- 7. 底部双栏结构 (Remark 备注 与 BANK INFORMATION 银行信息) -->
        <table class="pi-bottom-table">
          <thead>
            <tr>
              <th class="bottom-head bank-head">BANK INFORMATION:</th>
              <th class="bottom-head remark-head">Remark :</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <!-- 左侧 BANK INFORMATION 银行账号资料 -->
              <td class="bottom-cell bank-cell">
                <table class="bank-sub-table">
                  <tbody>
                    <tr>
                      <td class="bank-label">Beneficiary:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.beneficiary" class="inline-input" />
                        <span v-else>{{ piData.bank.beneficiary }}</span>
                      </td>
                    </tr>
                    <tr>
                      <td class="bank-label">BANK NAME:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.bank_name" class="inline-input" />
                        <span v-else>{{ piData.bank.bank_name }}</span>
                      </td>
                    </tr>
                    <tr>
                      <td class="bank-label">BANK ADDRESS:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.bank_address" class="inline-input" />
                        <span v-else>{{ piData.bank.bank_address }}</span>
                      </td>
                    </tr>
                    <tr>
                      <td class="bank-label">SWIFT BIC:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.swift_bic" class="inline-input" />
                        <span v-else>{{ piData.bank.swift_bic }}</span>
                      </td>
                    </tr>
                    <tr>
                      <td class="bank-label">Tel&Fax:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.tel_fax" class="inline-input" />
                        <span v-else>{{ piData.bank.tel_fax }}</span>
                      </td>
                    </tr>
                    <tr>
                      <td class="bank-label">Account No:</td>
                      <td class="bank-value">
                        <input v-if="isEditMode" v-model="piData.bank.account_no" class="inline-input" />
                        <span v-else>{{ piData.bank.account_no }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </td>

              <!-- 右侧 Remark 备注与条款 -->
              <td class="bottom-cell remark-cell">

                <div v-if="isEditMode" class="remark-edit-box">
                  <textarea
                    v-model="remarkInputText"
                    class="inline-textarea"
                    rows="8"
                    :style="{ fontSize: (piData.remark_font_size || 11) + 'px' }"
                    @blur="onRemarkInputBlur"
                  />
                </div>
                <div
                  v-else
                  class="remark-content"
                  :style="{ fontSize: (piData.remark_font_size || 11) + 'px' }"
                >
                  <div
                    v-for="(line, idx) in piData.remarks"
                    :key="idx"
                    class="remark-line"
                  >
                    {{ line }}
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 8. 双方签章区 (仅章印，章印可选，支持 backend/data/signatures 持久化) -->
        <table class="pi-signature-table">
          <thead>
            <tr>
              <th class="signature-head">The Seller's Signature and stamp</th>
              <th class="signature-gap"></th>
              <th class="signature-head">The Buyer's Signature and stamp</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <!-- 卖方签章框 -->
              <td class="signature-cell seller-signature-cell">
                <div class="signature-box">
                  <!-- 章印展示区 (可选) -->
                  <div v-if="piData.seller_stamp.show_stamp && piData.seller_stamp.stamp_url" class="seal-overlay">
                    <img :src="formatStampUrl(piData.seller_stamp.stamp_url)" alt="Seller Stamp" class="seal-img" />
                  </div>
                  <div v-else class="stamp-empty-placeholder">
                    <span>(卖方章印留白)</span>
                  </div>

                  <!-- 编辑模式下的控制控件：选择持久化章印与上传新章印 -->
                  <div v-if="isEditMode" class="stamp-controls no-print">
                    <el-checkbox v-model="piData.seller_stamp.show_stamp">显示卖方章印</el-checkbox>
                    <el-select
                      v-model="piData.seller_stamp.stamp_url"
                      placeholder="选择持久化签章"
                      size="small"
                      style="width: 140px"
                    >
                      <el-option
                        v-for="st in availableSignatures"
                        :key="st.url"
                        :label="st.filename"
                        :value="st.url"
                      />
                    </el-select>
                    <el-upload
                      action="#"
                      :auto-upload="false"
                      :show-file-list="false"
                      :on-change="handleStampUpload"
                      accept="image/*"
                    >
                      <el-button size="small" type="primary" plain>上传新章印</el-button>
                    </el-upload>
                  </div>
                </div>
              </td>

              <td class="signature-gap"></td>

              <!-- 买方签章框 -->
              <td class="signature-cell buyer-signature-cell">
                <div class="signature-box">
                  <div v-if="piData.buyer_stamp.show_stamp && piData.buyer_stamp.stamp_url" class="seal-overlay">
                    <img :src="formatStampUrl(piData.buyer_stamp.stamp_url)" alt="Buyer Stamp" class="seal-img" />
                  </div>
                  <div v-else class="stamp-empty-placeholder">
                    <span>(买方章印留白)</span>
                  </div>

                  <!-- 编辑模式控制买方章印 -->
                  <div v-if="isEditMode" class="stamp-controls no-print">
                    <el-checkbox v-model="piData.buyer_stamp.show_stamp">显示买方章印</el-checkbox>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview PI Excel 表头及全单据导出版头原型组件
 * 严格按照标准 PI Excel 文件样式对齐：
 * 1. 顶部公司大标题 + PI 编号 + 订单日期
 * 2. PROFORMA INVOICE 居中主标题
 * 3. 买方 (BUYER) 与 卖方 (SELLER) 双栏四行对齐格式
 * 4. 产品明细表严格 10 列标准结构：NAME | CODE | PHOTO | Description | Specification | pcs/ctn | Color | QTY | PRICE FOB | Amount
 * 5. 附加优惠行 (Additional benefits) + TOTAL 汇总行 + SAY TOTAL 大写总额
 * 6. 底部 Remark 备注与 BANK INFORMATION 银行信息
 */

import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Printer, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { apiUrl } from '@/api/base'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

const store = useOrderSummaryStore()

interface SignatureItem {
  filename: string
  url: string
}

/** 持久化签章文件列表 (读取 backend/data/signatures) */
const availableSignatures = ref<SignatureItem[]>([
  { filename: 'company_seal.png', url: '/data/signatures/company_seal.png' },
  { filename: 'signature1.png', url: '/data/signatures/signature1.png' },
  { filename: 'company_seal_stamp.png', url: '/company_seal_stamp.png' },
])

onMounted(async () => {
  try {
    const res = await fetch(apiUrl('/api/signatures'))
    if (res.ok) {
      const data = await res.json()
      if (data.success && Array.isArray(data.data) && data.data.length > 0) {
        availableSignatures.value = data.data
      }
    }
  } catch (err) {
    console.warn('获取 backend/data/signatures 签章列表失败', err)
  }
})

/** 组件 Props 属性定义 */
const props = withDefaults(
  defineProps<{
    isEditMode?: boolean
  }>(),
  {
    isEditMode: false,
  }
)

/** 内部本地编辑状态与外部 Prop 同步 */
const localEditMode = ref(false)
const isEditMode = computed({
  get: () => props.isEditMode || localEditMode.value,
  set: (val) => {
    localEditMode.value = val
  },
})

/** 导出 DOM 容器引用 */
const exportTargetRef = ref<HTMLElement | null>(null)

/** 买方信息接口 */
interface BuyerInfo {
  name: string
  tel: string
  address: string
  final_destination: string
}

/** 卖方信息接口 */
interface SellerInfo {
  contact: string
  tel_whatsapp: string
  address: string
  delivery_date: string
}

/** 10 列产品列表项接口 */
interface PiItem {
  name: string
  code: string
  photo?: string
  description: string
  specification: string
  pcs_ctn: string
  color: string
  qty: number
  unit_price: number
  amount_override?: number
  no_knife_icon?: boolean
}

/** 附加优惠接口 */
interface AdditionalBenefit {
  label: string
  amount: number
}

/** 银行信息接口 */
interface BankInfo {
  beneficiary: string
  bank_name: string
  bank_address: string
  swift_bic: string
  tel_fax: string
  account_no: string
}

/** 卖方签章接口 (只需章印，无姓名) */
interface SellerStamp {
  stamp_url: string
  show_stamp: boolean
}

/** 买方签章接口 (可选) */
interface BuyerStamp {
  stamp_url?: string
  show_stamp: boolean
}

/** PI 数据模型架构 */
interface PiDataModel {
  company_name: string
  pi_no: string
  order_date: string
  buyer: BuyerInfo
  seller: SellerInfo
  items: PiItem[]
  additional_benefits?: AdditionalBenefit
  say_total_override?: string
  remarks: string[]
  remark_font_size?: number
  bank: BankInfo
  seller_stamp: SellerStamp
  buyer_stamp: BuyerStamp
}

/** PI 响应式原型数据（完全匹配用户上传的 Excel 截图数据） */
const piData = reactive<PiDataModel>({
  company_name: 'HANGZHOU WEINA TRADE CO., LTD.',
  pi_no: 'SP260521',
  order_date: '2026/05/21',
  buyer: {
    name: 'Domator24',
    tel: '+48 725 484 888',
    address: 'ul. Dekoracyjna 10\n65-158 Zielona Góra\nNIP: 929207228863',
    final_destination: 'PL',
  },
  seller: {
    contact: 'Lisa chen',
    tel_whatsapp: '+86 132 8282 0031',
    address: 'Nanyuan Street, Lingping town of Hangzhou City, Zhejiang\nChina, ZIP CODE 311000\nTEL: 0086-571-86144203\nEmail: Lisa@viiner.com',
    delivery_date: '30 days after the deposit is paid',
  },
  items: [
    {
      name: 'Gaming Chair Model A',
      code: 'WM-8012',
      photo: '',
      description: 'Gaming Chair Ergonomic Design with Lumbar Support',
      specification: 'High Back / PU Leather',
      pcs_ctn: '1pcs/1ctn',
      color: 'Black/Red',
      qty: 970,
      unit_price: 22.85,
    },
    {
      name: 'Sample 1',
      code: '',
      photo: '',
      description: '/',
      specification: '/',
      pcs_ctn: '/',
      color: '',
      qty: 2,
      unit_price: 5.0,
      amount_override: 0,
      no_knife_icon: true,
    },
    {
      name: 'Accessories',
      code: '',
      photo: '',
      description: '',
      specification: '',
      pcs_ctn: '',
      color: '',
      qty: 10,
      unit_price: 65.0,
      amount_override: 0,
    },
  ],
  additional_benefits: {
    label: 'Additional benefits',
    amount: 35.0,
  },
  say_total_override: 'TWENTY-TWO THOUSAND TWO HUNDRED US DOLLARS ONLY',
  remarks: [
    'Should be have labels with a crossed knife to each box with pillows.\nThe label thread on the back of the seat cushion.',
    '1.Price Terms:FOB',
    '2.Payment Terms: T/T 10% deposit ,The 90% balance according to the BL.',
    '3. SHIPPING MARKS ARE BUYER\'S OPTION',
    'Warranty Time: 13 months after the shiping date',
  ],
  remark_font_size: 11,
  bank: {
    beneficiary: 'HANGZHOU WEINA TRADE CO.,LTD',
    bank_name: 'ZHEJIANG TAILONG COMMERCIAL BANK CO.,LTD',
    bank_address: 'LUQIAO TAIZHOU ZHEJIANG CHINA',
    swift_bic: 'ZJTLCNBH',
    tel_fax: 'Tel:+86-571-89178855',
    account_no: 'NRA33020020201000027051',
  },
  seller_stamp: {
    stamp_url: '/data/signatures/company_seal.png',
    show_stamp: true,
  },
  buyer_stamp: {
    stamp_url: '',
    show_stamp: false,
  },
})

/** 格式化日期字符串，仅保留年月日 (YYYY-MM-DD 或 YYYY/MM/DD) */
function formatDateOnly(dateStr?: string): string {
  if (!dateStr) return ''
  const str = String(dateStr).trim()
  if (str.includes('T')) {
    return str.split('T')[0]
  }
  if (str.includes(' ')) {
    return str.split(' ')[0]
  }
  return str
}

/** 应用并同步单据编辑数据至当前 PI 渲染模型 */
function applyExportData(data: any) {
  if (!data) return
  if (data.company_name) piData.company_name = data.company_name
  if (data.pi_no) piData.pi_no = data.pi_no
  if (data.order_date) piData.order_date = formatDateOnly(data.order_date)
  if (data.buyer) Object.assign(piData.buyer, data.buyer)
  if (data.seller) Object.assign(piData.seller, data.seller)
  if (Array.isArray(data.items)) piData.items = JSON.parse(JSON.stringify(data.items))
  if (data.additional_benefits) {
    if (piData.additional_benefits) {
      Object.assign(piData.additional_benefits, data.additional_benefits)
    } else {
      piData.additional_benefits = { ...data.additional_benefits }
    }
  }
  if (Array.isArray(data.remarks)) piData.remarks = [...data.remarks]
  if (typeof data.remark_font_size === 'number') piData.remark_font_size = data.remark_font_size
  if (data.bank) Object.assign(piData.bank, data.bank)
  if (data.seller_stamp) Object.assign(piData.seller_stamp, data.seller_stamp)
  if (data.buyer_stamp) Object.assign(piData.buyer_stamp, data.buyer_stamp)
}

watch(
  () => store.exportDocData,
  (newVal) => {
    if (newVal) {
      applyExportData(newVal)
    }
  },
  { immediate: true, deep: true }
)

/** 格式化章印图片的显示 URL */
function formatStampUrl(url?: string): string {
  if (!url) return '/data/signatures/company_seal.png'
  if (url.startsWith('data:image/') || url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return apiUrl(url)
}

/** 上传或替换电子印章图片 */
function handleStampUpload(uploadFile: any) {
  const rawFile = uploadFile.raw
  if (!rawFile) return
  const reader = new FileReader()
  reader.onload = (e) => {
    if (e.target?.result) {
      piData.seller_stamp.stamp_url = e.target.result as string
      ElMessage.success('电子印章更新成功！')
    }
  }
  reader.readAsDataURL(rawFile)
}

/** 编辑模式下 Remark 多行文本 */
const remarkInputText = ref(piData.remarks.join('\n\n'))

function onRemarkInputBlur() {
  piData.remarks = remarkInputText.value.split(/\n\n+/).filter(Boolean)
}


/** 计算单个产品项小计 */
function getItemAmount(item: PiItem): number {
  if (item.amount_override !== undefined) {
    return item.amount_override
  }
  return item.qty * item.unit_price
}

/** 将数字金额转化为标准美语大写金额描述 (例如 55.00 -> FIFTY-FIVE US DOLLARS ONLY) */
function numberToEnglishWords(num: number): string {
  if (num <= 0) return 'ZERO US DOLLARS ONLY'
  const integerPart = Math.floor(num)
  const cents = Math.round((num - integerPart) * 100)

  const ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN',
    'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
  const tens = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY']

  function convertChunk(n: number): string {
    let str = ''
    if (n >= 100) {
      str += ones[Math.floor(n / 100)] + ' HUNDRED '
      n %= 100
    }
    if (n >= 20) {
      str += tens[Math.floor(n / 10)] + (n % 10 !== 0 ? '-' + ones[n % 10] : '') + ' '
    } else if (n > 0) {
      str += ones[n] + ' '
    }
    return str.trim()
  }

  let words = ''
  let n = integerPart

  if (n >= 1000000) {
    const millions = Math.floor(n / 1000000)
    words += convertChunk(millions) + ' MILLION '
    n %= 1000000
  }
  if (n >= 1000) {
    const thousands = Math.floor(n / 1000)
    words += convertChunk(thousands) + ' THOUSAND '
    n %= 1000
  }
  if (n > 0) {
    words += convertChunk(n) + ' '
  }

  words = words.trim()
  let result = words ? `${words} US DOLLARS` : 'ZERO US DOLLARS'
  if (cents > 0) {
    result += ` AND ${convertChunk(cents)} CENTS`
  }
  return `${result} ONLY`
}

/** 计算产品总数量 */
const totalQuantity = computed(() => {
  return piData.items.reduce((sum, item) => sum + item.qty, 0)
})

/** 计算产品总金额 (含 Additional benefits) */
const totalAmount = computed(() => {
  const itemsSum = piData.items.reduce((sum, item) => sum + getItemAmount(item), 0)
  const benefits = piData.additional_benefits?.amount || 0
  return itemsSum + benefits
})

/** SAY TOTAL 英文大写描述 (支持精确动态转换与手写覆写) */
const sayTotalText = computed(() => {
  if (piData.say_total_override && piData.say_total_override !== 'TWENTY-TWO THOUSAND TWO HUNDRED US DOLLARS ONLY') {
    return piData.say_total_override
  }
  return numberToEnglishWords(totalAmount.value)
})

/** 格式化金额千分位 */
function formatMoney(val: number): string {
  return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 调起原生浏览器打印/另存为 PDF */
function handlePrint() {
  window.print()
}

/** 调起浏览器打印对话框保存为 PDF */
function handleExportPdf() {
  ElMessage.info('请在弹出的打印窗口中选择「另存为 PDF」')
  window.print()
}

/** 导出当前 PI 数据为 Excel 文件（包含 10 列结构、合并单元格 !merges 与 列宽 !cols 配置） */
function handleExportExcel() {
  try {
    const formattedPiNo = piData.pi_no || store.currentOrder?.pi_no || 'SP260521'
    const formattedOrderDate = formatDateOnly(piData.order_date || store.currentOrder?.created_at || '2026/05/21')

    const wsData: any[][] = [
      // Row 1: Company Title (A1:J1)
      [piData.company_name, '', '', '', '', '', '', '', '', ''],
      // Row 2: PI. NO. (A2:E2) & Order Date (F2:J2)
      ['PI. NO. :', formattedPiNo, '', '', '', 'Order Date:', formattedOrderDate, '', '', ''],
      // Row 3: PROFORMA INVOICE Title (A3:J3)
      ['PROFORMA INVOICE', '', '', '', '', '', '', '', '', ''],
      // Row 4: Section Headers (A4:E4 & F4:J4)
      ['BUYER (买方信息)', '', '', '', '', 'SELLER:（卖方信息）', '', '', '', ''],
      // Row 5: TO vs Contact
      ['TO:', piData.buyer.name || '', '', '', '', 'Contact:', piData.seller.contact || '', '', '', ''],
      // Row 6: Tel vs Tel/WhatsApp
      ['Tel:', piData.buyer.tel || '', '', '', '', 'Tel/WhatsApp:', piData.seller.tel_whatsapp || '', '', '', ''],
      // Row 7: ADDRESS vs ADDRESS
      ['ADDRESS:', piData.buyer.address || '', '', '', '', 'ADDRESS:', piData.seller.address || '', '', '', ''],
      // Row 8: Final Destination vs Delivery date
      ['Final Destination:', piData.buyer.final_destination || '', '', '', '', 'Delivery date:', piData.seller.delivery_date || '', '', '', ''],
      // Row 9: Empty
      ['', '', '', '', '', '', '', '', '', ''],
      // Row 10: Product Items Header (10 columns A to J)
      ['NAME', 'CODE', 'PHOTO', 'Description', 'Specification', 'pcs/ctn', 'Color', 'QTY', 'PRICE FOB', 'Amount'],
    ]

    // 明细行
    piData.items.forEach((it) => {
      wsData.push([
        it.name,
        it.code,
        it.no_knife_icon ? '[NO KNIFE]' : '[PHOTO]',
        it.description,
        it.specification,
        it.pcs_ctn,
        it.color,
        it.qty,
        it.unit_price,
        getItemAmount(it),
      ])
    })

    // Additional benefits
    if (piData.additional_benefits) {
      wsData.push([piData.additional_benefits.label, '', '', '', '', '', '', '', '', piData.additional_benefits.amount])
    }

    // TOTAL row
    wsData.push(['TOTAL :', '', '', '', '', '', '', totalQuantity.value, '', totalAmount.value])
    // SAY TOTAL row
    wsData.push([`SAY TOTAL: ${sayTotalText.value}`, '', '', '', '', '', '', '', '', ''])
    // Blank row
    wsData.push(['', '', '', '', '', '', '', '', '', ''])
    // Remark & BANK INFORMATION
    wsData.push(['Remark :', '', '', '', '', 'BANK INFORMATION:', '', '', '', ''])
    wsData.push([piData.remarks.join('\n'), '', '', '', '', `Beneficiary: ${piData.bank.beneficiary}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', `BANK NAME: ${piData.bank.bank_name}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', `BANK ADDRESS: ${piData.bank.bank_address}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', `SWIFT BIC: ${piData.bank.swift_bic}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', `Tel&Fax: ${piData.bank.tel_fax}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', `Account No: ${piData.bank.account_no}`, '', '', '', ''])
    wsData.push(['', '', '', '', '', '', '', '', '', ''])
    wsData.push(["The Seller's Signature and stamp", '', '', '', '', "The Buyer's Signature and stamp", '', '', '', ''])
    wsData.push([
      piData.seller_stamp.show_stamp ? '[SELLER STAMP INCLUDED]' : '(No Stamp)',
      '',
      '',
      '',
      '',
      piData.buyer_stamp.show_stamp ? '[BUYER STAMP INCLUDED]' : '(No Stamp)',
      '',
      '',
      '',
      '',
    ])

    const ws = XLSX.utils.aoa_to_sheet(wsData)

    // 列宽配置 (!cols)
    ws['!cols'] = [
      { wch: 18 }, // A: NAME
      { wch: 16 }, // B: CODE
      { wch: 10 }, // C: PHOTO
      { wch: 28 }, // D: Description
      { wch: 16 }, // E: Specification
      { wch: 14 }, // F: pcs/ctn
      { wch: 12 }, // G: Color
      { wch: 8 },  // H: QTY
      { wch: 12 }, // I: PRICE FOB
      { wch: 14 }, // J: Amount
    ]

    // 行高配置 (!rows) - 解决 Excel 导出后文字及明细行拥挤变形问题
    const rowsConfig: Array<{ hpt: number }> = [
      { hpt: 32 }, // Row 1: 公司大标题 A1:J1
      { hpt: 22 }, // Row 2: PI. NO. & Order Date
      { hpt: 28 }, // Row 3: PROFORMA INVOICE 标题
      { hpt: 24 }, // Row 4: BUYER & SELLER 标题栏
      { hpt: 20 }, // Row 5: TO vs Contact
      { hpt: 20 }, // Row 6: Tel vs Tel/WhatsApp
      { hpt: 24 }, // Row 7: ADDRESS vs ADDRESS
      { hpt: 20 }, // Row 8: Final Destination vs Delivery date
      { hpt: 12 }, // Row 9: 空白间隔行
      { hpt: 26 }, // Row 10: 产品表头 (NAME, CODE, PHOTO...)
    ]

    // 为每个商品明细设置 45pt 行高，保证图片标识与文字空间充裕
    piData.items.forEach(() => {
      rowsConfig.push({ hpt: 45 })
    })

    // Additional benefits 行
    if (piData.additional_benefits) {
      rowsConfig.push({ hpt: 24 })
    }

    // TOTAL 汇总行
    rowsConfig.push({ hpt: 26 })
    // SAY TOTAL 行
    rowsConfig.push({ hpt: 26 })
    // 空白间隔行
    rowsConfig.push({ hpt: 12 })
    // Remark & BANK INFORMATION 标题行
    rowsConfig.push({ hpt: 24 })
    // Bank Details & Remark 内容 7 行
    for (let i = 0; i < 7; i++) {
      rowsConfig.push({ hpt: 20 })
    }
    // 空白间隔行
    rowsConfig.push({ hpt: 12 })
    // 双方签署标题行
    rowsConfig.push({ hpt: 24 })
    // 双方印章/盖章行
    rowsConfig.push({ hpt: 45 })

    ws['!rows'] = rowsConfig

    // 单元格合并规则配置 (!merges)
    const merges = [
      { s: { r: 0, c: 0 }, e: { r: 0, c: 9 } }, // A1:J1 公司大标题
      { s: { r: 1, c: 1 }, e: { r: 1, c: 4 } }, // B2:E2 PI. NO.
      { s: { r: 1, c: 6 }, e: { r: 1, c: 9 } }, // G2:J2 Order Date
      { s: { r: 2, c: 0 }, e: { r: 2, c: 9 } }, // A3:J3 PROFORMA INVOICE 标题
      { s: { r: 3, c: 0 }, e: { r: 3, c: 4 } }, // A4:E4 BUYER 标题
      { s: { r: 3, c: 5 }, e: { r: 3, c: 9 } }, // F4:J4 SELLER 标题
      { s: { r: 4, c: 1 }, e: { r: 4, c: 4 } }, // B5:E5 Buyer Name
      { s: { r: 4, c: 6 }, e: { r: 4, c: 9 } }, // G5:J5 Seller Contact
      { s: { r: 5, c: 1 }, e: { r: 5, c: 4 } }, // B6:E6 Buyer Tel
      { s: { r: 5, c: 6 }, e: { r: 5, c: 9 } }, // G6:J6 Seller Tel
      { s: { r: 6, c: 1 }, e: { r: 6, c: 4 } }, // B7:E7 Buyer Address
      { s: { r: 6, c: 6 }, e: { r: 6, c: 9 } }, // G7:J7 Seller Address
      { s: { r: 7, c: 1 }, e: { r: 7, c: 4 } }, // B8:E8 Buyer Destination
      { s: { r: 7, c: 6 }, e: { r: 7, c: 9 } }, // G8:J8 Seller Delivery Date
    ]

    const itemsCount = piData.items.length
    let currentRow = 10 + itemsCount
    if (piData.additional_benefits) {
      merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 8 } })
      currentRow++
    }

    // TOTAL 行
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 6 } })
    currentRow++

    // SAY TOTAL 行
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 9 } })
    currentRow += 2

    // Remark & BANK INFORMATION 标题行
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 4 } })
    merges.push({ s: { r: currentRow, c: 5 }, e: { r: currentRow, c: 9 } })
    currentRow++

    // Bank Details 7 行
    for (let i = 0; i < 7; i++) {
      merges.push({ s: { r: currentRow + i, c: 5 }, e: { r: currentRow + i, c: 9 } })
    }
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow + 6, c: 4 } })
    currentRow += 8

    // Signatures
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 4 } })
    merges.push({ s: { r: currentRow, c: 5 }, e: { r: currentRow, c: 9 } })
    currentRow++
    merges.push({ s: { r: currentRow, c: 0 }, e: { r: currentRow, c: 4 } })
    merges.push({ s: { r: currentRow, c: 5 }, e: { r: currentRow, c: 9 } })

    ws['!merges'] = merges

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'PI')
    XLSX.writeFile(wb, `PI_${formattedPiNo}.xlsx`)
    ElMessage.success('Excel 高保真表格导出成功！')
  } catch (err) {
    ElMessage.error('导出失败：' + (err as Error).message)
  }
}

/** 显式暴露导出方法给 Unified ExportPreview 组件使用 */
defineExpose({
  handleExportExcel,
  handlePrint,
})
</script>

<style scoped>
/* 8. 双方签章区 (The Seller's Signature and stamp vs The Buyer's Signature and stamp) */
.pi-signature-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
  table-layout: fixed;
}

.signature-head {
  width: 48%;
  font-size: 12px;
  font-weight: bold;
  text-align: center;
  padding-bottom: 6px;
}

.signature-gap {
  width: 4%;
}

.signature-cell {
  vertical-align: top;
}

.signature-box {
  border: 1px solid #000000;
  height: 110px;
  padding: 8px;
  position: relative;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stamp-empty-placeholder {
  font-size: 11px;
  color: #909399;
  font-style: italic;
}

/* 电子印章覆盖居中透明层 */
.seal-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
  pointer-events: none;
}

.seal-img {
  max-width: 190px;
  max-height: 95px;
  opacity: 0.88;
  mix-blend-mode: multiply;
  filter: contrast(120%);
}

.stamp-controls {
  position: absolute;
  bottom: 4px;
  left: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  z-index: 5;
  background: rgba(255, 255, 255, 0.92);
  padding: 2px 6px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* 整个页面容器：独立 100vh 垂直滚动 */
.pi-export-container {
  padding: 24px;
  background-color: #f5f7fa;
  height: 100vh;
  overflow-y: auto;
  box-sizing: border-box;
  font-family: 'Times New Roman', Times, SimSun, Georgia, serif;
}

/* 顶部操作工具栏 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.action-bar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  font-family: system-ui, -apple-system, sans-serif;
}

/* PI 单据包裹容器（仿真 A4/Excel 打印体验） */
.pi-sheet-wrapper {
  display: flex;
  justify-content: center;
}

.pi-sheet {
  width: 210mm;
  min-height: 297mm;
  padding: 15mm 15mm;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  color: #000000;
}

/* 1. 卖方公司英文大标题 */
.company-header-title {
  text-align: center;
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 0.5px;
  line-height: 1.3;
  margin-bottom: 8px;
  text-transform: uppercase;
}

/* 2. PI NO. 与 Order Date 行 */
.pi-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 6px;
  padding: 0 4px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-hint {
  color: #d90000;
  font-style: italic;
  font-weight: normal;
  font-size: 12px;
  margin-left: 6px;
}

/* 3. PROFORMA INVOICE 居中大标题 */
.pi-main-title {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 1px;
  margin-bottom: 12px;
}

/* 4. 双栏表格（BUYER vs SELLER） */
.pi-info-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  table-layout: fixed;
}

.pi-info-table th,
.pi-info-table td {
  border: 1px solid #000000;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 1.4;
  vertical-align: middle;
}

.pi-info-table th.section-head {
  background-color: #f2f2f2;
  text-align: center;
  font-weight: bold;
  font-size: 13px;
  padding: 6px;
}

.label-col {
  width: 18%;
  font-weight: bold;
}

.content-col {
  width: 32%;
}

.align-top {
  vertical-align: top !important;
  padding-top: 6px !important;
}

.multiline-text {
  white-space: pre-line;
  word-break: break-word;
}

/* 可编辑内联控件样式 */
.inline-input {
  width: 100%;
  border: 1px dashed #409eff;
  background: #f0f7ff;
  font-family: inherit;
  font-size: inherit;
  padding: 2px 4px;
  box-sizing: border-box;
}

.inline-textarea {
  width: 100%;
  border: 1px dashed #409eff;
  background: #f0f7ff;
  font-family: inherit;
  font-size: inherit;
  padding: 2px 4px;
  box-sizing: border-box;
  resize: vertical;
}

/* 5. 产品明细表格 */
.pi-items-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.pi-items-table th,
.pi-items-table td {
  border: 1px solid #000000;
  padding: 6px 8px;
  font-size: 12px;
  vertical-align: middle;
}

.pi-items-table th {
  background-color: #f2f2f2;
  text-align: center;
  font-weight: bold;
}

.photo-placeholder {
  width: 50px;
  height: 36px;
  background-color: #f5f7fa;
  border: 1px dashed #dcdfe6;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #909399;
}

.text-left {
  text-align: left;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.text-red {
  color: #d90000 !important;
}

.yellow-bg {
  background-color: #fff2cc !important;
}

/* 禁刀图标样式 (No crossed knife) */
.no-knife-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 2px solid #d90000;
  border-radius: 50%;
  position: relative;
  font-size: 14px;
}

.no-knife-icon .cross-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background-color: #d90000;
  transform: rotate(-45deg);
}

/* 附加优惠行 (Additional benefits) */
.additional-benefits-row td {
  padding: 6px 8px;
}

/* TOTAL 汇总行 */
.total-summary-row td {
  border-top: 2px solid #000000 !important;
  font-size: 16px;
  padding: 8px;
}

.total-title-col {
  font-size: 18px;
  letter-spacing: 2px;
}

.total-qty-col {
  font-size: 16px;
}

.total-amount-col {
  font-size: 18px;
}

/* SAY TOTAL 大写总额行 */
.say-total-row {
  margin-top: 8px;
  margin-bottom: 12px;
  padding: 6px 8px;
  border: 1px solid #000000;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  gap: 8px;
}

.say-total-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.say-total-value {
  text-transform: uppercase;
}

/* 7. 底部 Remark 与 BANK INFORMATION 表格 */
.pi-bottom-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  table-layout: fixed;
}

.pi-bottom-table th,
.pi-bottom-table td {
  border: 1px solid #000000;
  padding: 6px 8px;
  font-size: 11px;
  vertical-align: top;
}

.bottom-head {
  background-color: #f2f2f2;
  font-weight: bold;
  font-size: 12px;
  padding: 6px;
}

.remark-head {
  width: 50%;
  text-align: center;
}

.bank-head {
  width: 50%;
  text-align: center;
}

.remark-cell {
  line-height: 1.5;
}


.remark-line {
  margin-bottom: 6px;
  white-space: pre-line;
}

.bank-sub-table {
  width: 100%;
  border-collapse: collapse;
}

.bank-sub-table td {
  border: none !important;
  padding: 3px 4px;
  font-size: 11px;
}

.bank-label {
  width: 32%;
  font-weight: bold;
  white-space: nowrap;
}

.bank-value {
  width: 68%;
  font-family: inherit;
}

/* 打印专用的 CSS 媒体查询：导出或打印时隐藏按钮及边框线 */
@media print {
  .no-print {
    display: none !important;
  }
  .pi-export-container {
    padding: 0;
    background: none;
    height: auto !important;
    overflow: visible !important;
  }
  .pi-sheet {
    box-shadow: none;
    width: 100%;
    padding: 0;
  }
  .inline-input,
  .inline-textarea {
    border: none !important;
    background: none !important;
  }
}
</style>
