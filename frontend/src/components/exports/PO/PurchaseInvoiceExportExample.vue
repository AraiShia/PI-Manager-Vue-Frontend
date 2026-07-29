<template>
  <div class="purchase-sheet-wrapper">
    <div class="purchase-sheet">
      <!-- 1. 顶部绿色边框线与大标题 -->
      <div class="top-green-line"></div>
      <h1 class="company-title">{{ purchaseData.company_name }}</h1>

      <!-- 2. 合同类型黑框条 -->
      <div class="contract-header-bar">
        <span class="contract-header-title">采 购 合 同</span>
      </div>

      <!-- 3. 合同编号与日期行 -->
      <div class="contract-meta-row">
        <div class="meta-left">
          <strong>合 同 编 号：</strong>
          <span class="formula-hint">{{ purchaseData.po_no_formula }}</span>
          <span class="po-no">（{{ purchaseData.pi_no }}）</span>
        </div>
        <div class="meta-right">
          <strong>合 同 日 期：</strong> {{ purchaseData.order_date }}
        </div>
      </div>

      <!-- 4. 买卖双方信息表格 -->
      <table class="party-info-table">
        <tr class="seal-prompt-row">
          <td colspan="2" class="text-left font-bold border-right">卖方 (盖章)</td>
          <td colspan="2" class="text-left font-bold">买方 (盖章)</td>
        </tr>
        <tr>
          <td class="label-col">供 应 商</td>
          <td class="val-col border-right">{{ purchaseData.seller.name }}</td>
          <td class="label-col">采 购 商</td>
          <td class="val-col">{{ purchaseData.buyer.name }}</td>
        </tr>
        <tr>
          <td class="label-col">联 系 人</td>
          <td class="val-col border-right">{{ purchaseData.seller.contact }}</td>
          <td class="label-col">联 系 人</td>
          <td class="val-col">{{ purchaseData.buyer.contact }}</td>
        </tr>
        <tr>
          <td class="label-col">联系电话</td>
          <td class="val-col border-right">{{ purchaseData.seller.phone }}</td>
          <td class="label-col">联系电话</td>
          <td class="val-col">{{ purchaseData.buyer.phone }}</td>
        </tr>
        <tr>
          <td class="label-col">地 址</td>
          <td class="val-col border-right">{{ purchaseData.seller.address }}</td>
          <td class="label-col">地 址</td>
          <td class="val-col">{{ purchaseData.buyer.address }}</td>
        </tr>
      </table>

      <!-- 5. 12 列明细表格 -->
      <table class="purchase-items-table mt-3">
        <thead>
          <tr>
            <th style="width: 5%">图片</th>
            <th style="width: 10%">
              维那型号<br />
              <span class="text-danger">客户编号</span>
            </th>
            <th style="width: 9%">工厂型号</th>
            <th style="width: 10%">产品名称</th>
            <th style="width: 13%">描述</th>
            <th style="width: 8%">规格/CM</th>
            <th style="width: 9%">外包装尺寸</th>
            <th style="width: 6%">数量</th>
            <th style="width: 5%">单位</th>
            <th style="width: 8%">净重/毛重</th>
            <th style="width: 8%">单价 (含税)</th>
            <th style="width: 9%">总金额 (含税)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in purchaseData.items" :key="index">
            <td class="text-center">
              <img v-if="item.image_url" :src="item.image_url" class="item-img" alt="product" />
              <span v-else class="text-gray">-</span>
            </td>
            <td class="text-center">
              <div>{{ item.weina_code || item.code }}</div>
              <div class="text-danger font-bold">{{ item.customer_code }}</div>
            </td>
            <td class="text-center">{{ item.factory_code || '-' }}</td>
            <td>{{ item.name }}</td>
            <td class="text-desc">{{ item.description || item.detail_requirement || '-' }}</td>
            <td class="text-center">{{ item.spec || item.specification || '-' }}</td>
            <td class="text-center">{{ item.pack_size || item.package_size || '-' }}</td>
            <td class="text-center font-bold">{{ item.qty }}</td>
            <td class="text-center">{{ item.unit || '个' }}</td>
            <td class="text-center">{{ item.nw_gw || '-' }}</td>
            <td class="text-right">¥{{ formatMoney(item.unit_price) }}</td>
            <td class="text-right font-bold">¥{{ formatMoney(item.qty * item.unit_price) }}</td>
          </tr>
        </tbody>
        <!-- 6. 总计行 -->
        <tfoot>
          <tr class="total-row">
            <td colspan="7" class="text-center font-bold">总计</td>
            <td class="text-center font-bold">{{ totalQuantity }}</td>
            <td colspan="3"></td>
            <td class="text-right font-bold text-lg">¥{{ formatMoney(totalAmount) }}</td>
          </tr>
        </tfoot>
      </table>

      <!-- 7. 下半部分：约定与条款表格 -->
      <table class="terms-table mt-2">
        <tr>
          <td class="terms-label">产品要求</td>
          <td colspan="3" class="terms-val text-danger font-bold">
            {{ purchaseData.product_requirement }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">包装要求</td>
          <td colspan="3" class="terms-val">
            {{ purchaseData.package_requirement }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">交货日期</td>
          <td colspan="3" class="terms-val">
            {{ purchaseData.delivery_date }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">交货地址</td>
          <td colspan="3" class="terms-val">
            {{ purchaseData.delivery_address }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">供应商收款名称</td>
          <td class="terms-val" style="width: 40%">
            {{ purchaseData.supplier_bank_name || purchaseData.seller.name }}
          </td>
          <td class="terms-label" style="width: 15%">收货联系人</td>
          <td class="terms-val" style="width: 25%">
            {{ purchaseData.receiver_contact || purchaseData.buyer.contact }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">开发行及账号</td>
          <td class="terms-val">
            {{ purchaseData.supplier_bank_account }}
          </td>
          <td class="terms-label">联系电话</td>
          <td class="terms-val">
            {{ purchaseData.receiver_phone || purchaseData.seller.phone }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">付款方式</td>
          <td colspan="3" class="terms-val">
            {{ purchaseData.payment_method }}
          </td>
        </tr>
        <tr>
          <td class="terms-label">备注</td>
          <td colspan="3" class="terms-val">
            {{ purchaseData.remarks || '' }}
          </td>
        </tr>
      </table>

      <!-- 8. 四条标准合同条款 -->
      <div class="clauses-wrapper mt-3">
        <div class="clauses-title-bar">
          <strong>合同条款：</strong>
        </div>
        <ol class="clauses-list">
          <li v-for="(clause, idx) in purchaseData.clauses" :key="idx">
            {{ clause }}
          </li>
        </ol>
      </div>

      <!-- 9. 底部双框签章签署区域 -->
      <div class="signature-boxes-container mt-4">
        <!-- 卖方印章框 -->
        <div class="sig-box">
          <div class="sig-title">
            <strong>卖方：</strong> {{ purchaseData.sign_seller.name || purchaseData.seller.name }}
          </div>
          <div class="sig-line">
            <strong>单位名称(公章)：</strong>
          </div>
          <div class="sig-line">
            <strong>单位地址：</strong> {{ purchaseData.sign_seller.address || purchaseData.seller.address }}
          </div>
          <div class="sig-line">
            <strong>联系人：</strong> {{ purchaseData.sign_seller.contact || purchaseData.seller.contact }}
          </div>
          <div class="sig-line">
            <strong>电话：</strong> {{ purchaseData.sign_seller.phone || purchaseData.seller.phone }}
          </div>
          <!-- 盖章公章图层 -->
          <div v-if="purchaseData.sign_seller.show_stamp && purchaseData.sign_seller.stamp_url" class="stamp-overlay">
            <img :src="purchaseData.sign_seller.stamp_url" alt="Seller Stamp" />
          </div>
        </div>

        <!-- 买方印章框 -->
        <div class="sig-box">
          <div class="sig-title">
            <strong>买方：</strong> {{ purchaseData.sign_buyer.name || purchaseData.buyer.name }}
          </div>
          <div class="sig-line">
            <strong>单位名称(公章)：</strong>
          </div>
          <div class="sig-line">
            <strong>单位地址：</strong> {{ purchaseData.sign_buyer.address || purchaseData.buyer.address }}
          </div>
          <div class="sig-line">
            <strong>联系人：</strong> {{ purchaseData.sign_buyer.contact || purchaseData.buyer.contact }}
          </div>
          <div class="sig-line">
            <strong>电话：</strong> {{ purchaseData.sign_buyer.phone || purchaseData.buyer.phone }}
          </div>
          <!-- 盖章公章图层 -->
          <div v-if="purchaseData.sign_buyer.show_stamp && purchaseData.sign_buyer.stamp_url" class="stamp-overlay">
            <img :src="purchaseData.sign_buyer.stamp_url" alt="Buyer Stamp" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview Purchase Contract 采购合同高保真渲染与导出组件 (与采购合同模板100%精准对齐)
 */

import { reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

const props = withDefaults(defineProps<{ isEditMode?: boolean }>(), { isEditMode: false })
const store = useOrderSummaryStore()

export interface PurchaseItem {
  image_url?: string
  weina_code?: string
  code?: string
  customer_code?: string
  factory_code?: string
  name: string
  description?: string
  detail_requirement?: string
  spec?: string
  specification?: string
  pack_size?: string
  package_size?: string
  qty: number
  unit?: string
  nw_gw?: string
  unit_price: number
}

export interface PartyInfo {
  name: string
  contact: string
  phone: string
  address: string
}

export interface StampInfo {
  name?: string
  address?: string
  contact?: string
  phone?: string
  show_stamp: boolean
  stamp_url: string
}

export interface PurchaseDataModel {
  company_name: string
  pi_no: string
  po_no_formula: string
  order_date: string
  seller: PartyInfo
  buyer: PartyInfo
  items: PurchaseItem[]
  product_requirement: string
  package_requirement: string
  delivery_date: string
  delivery_address: string
  supplier_bank_name: string
  supplier_bank_account: string
  receiver_contact: string
  receiver_phone: string
  payment_method: string
  remarks: string
  clauses: string[]
  sign_seller: StampInfo
  sign_buyer: StampInfo
}

const purchaseData = reactive<PurchaseDataModel>({
  company_name: '杭州维那贸易有限公司',
  pi_no: 'XLW2204171',
  po_no_formula: '供应商编号 + 维那编号 +采购日期 +序号',
  order_date: '2025年4月17日',
  seller: {
    name: '安吉大龙家具有限公司',
    contact: 'Jack Liu',
    phone: '0572-5718520  18857325120',
    address: '浙江省安吉县康山工业园',
  },
  buyer: {
    name: '杭州维那贸易有限公司',
    contact: 'Jacky',
    phone: '18069766520',
    address: '',
  },
  items: [
    {
      image_url: '',
      weina_code: 'WM-8012',
      customer_code: 'CUST-8012',
      factory_code: 'FL-8012-A',
      name: '电竞椅高级黑色款',
      description: '人体工学网椅，双弹簧防爆底盘',
      spec: '68*68*125',
      pack_size: '85*65*32',
      qty: 80,
      unit: '件',
      nw_gw: '15.5/17.2',
      unit_price: 635.0,
    },
  ],
  product_requirement: '无褶皱，清洁无线头，无银光笔笔痕，logo不能倾斜，正确区分青蛙托坐垫跟蝴蝶托坐垫',
  package_requirement: '300磅五层双瓦纸箱，内加EPE打包方式',
  delivery_date: '2025/05/18日前',
  delivery_address: '送到买方指定仓库（卖方负责运输费用）',
  supplier_bank_name: '安吉大龙家具有限公司',
  supplier_bank_account: '湖州银行股份有限公司安吉支行    811265887000909',
  receiver_contact: 'Jacky',
  receiver_phone: '18857325120',
  payment_method: '下好订单，卖方确认合同盖章后付预付款；预付款30%，剩余款装货前付清',
  remarks: '',
  clauses: [
    '1. 本合同自签订之日起，盖章签字后生效。如需修改或终止时，应经双方协商同意，另立协议方可有效。',
    '2. 本合同在执行期间任何一方违约，由双方协商解决，违约需赔偿损失。',
    '3. 买方接收货物，视为卖方履行生产义务；检验不合格的部件由卖方补发，买方根据情况要求卖方承担相应的违约责任。',
    '4. 在未达成新的协议前，卖方如需调整价格，需提前一个月向买方协商，同时卖方不得影响买方的正常供货。',
  ],
  sign_seller: {
    name: '安吉大龙家具有限公司',
    address: '',
    contact: '',
    phone: '',
    show_stamp: false,
    stamp_url: '',
  },
  sign_buyer: {
    name: '杭州维那贸易有限公司',
    address: '浙江省杭州市临平区南苑街道石门街6号2007',
    contact: '李荣军',
    phone: '0571-86131966',
    show_stamp: true,
    stamp_url: '/data/signatures/company_seal.png',
  },
})

function applyExportData(data: any) {
  if (!data) return
  if (data.company_name) purchaseData.company_name = data.company_name
  if (data.pi_no) purchaseData.pi_no = data.pi_no
  if (data.po_no_formula) purchaseData.po_no_formula = data.po_no_formula
  if (data.order_date) purchaseData.order_date = data.order_date

  if (data.seller) Object.assign(purchaseData.seller, data.seller)
  if (data.buyer) Object.assign(purchaseData.buyer, data.buyer)

  if (Array.isArray(data.items) && data.items.length > 0) {
    purchaseData.items = JSON.parse(JSON.stringify(data.items))
  }

  if (data.product_requirement) purchaseData.product_requirement = data.product_requirement
  if (data.package_requirement) purchaseData.package_requirement = data.package_requirement
  if (data.delivery_date) purchaseData.delivery_date = data.delivery_date
  if (data.delivery_address) purchaseData.delivery_address = data.delivery_address
  if (data.supplier_bank_name) purchaseData.supplier_bank_name = data.supplier_bank_name
  if (data.supplier_bank_account) purchaseData.supplier_bank_account = data.supplier_bank_account
  if (data.receiver_contact) purchaseData.receiver_contact = data.receiver_contact
  if (data.receiver_phone) purchaseData.receiver_phone = data.receiver_phone
  if (data.payment_method) purchaseData.payment_method = data.payment_method
  if (data.remarks !== undefined) purchaseData.remarks = data.remarks

  if (data.seller_stamp) {
    purchaseData.sign_seller.show_stamp = data.seller_stamp.show_stamp ?? false
    if (data.seller_stamp.stamp_url) purchaseData.sign_seller.stamp_url = data.seller_stamp.stamp_url
  }
  if (data.buyer_stamp) {
    purchaseData.sign_buyer.show_stamp = data.buyer_stamp.show_stamp ?? true
    if (data.buyer_stamp.stamp_url) purchaseData.sign_buyer.stamp_url = data.buyer_stamp.stamp_url
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
      [purchaseData.company_name],
      ['采 购 合 同'],
      [`合同编号：${purchaseData.po_no_formula} (${purchaseData.pi_no})`, '', '', '', '', '', '', `合同日期：${purchaseData.order_date}`],
      ['卖方 (盖章)', '', '', '', '', '', '买方 (盖章)'],
      [`供应商`, purchaseData.seller.name, '', '', '', '', `采购商`, purchaseData.buyer.name],
      [`联系人`, purchaseData.seller.contact, '', '', '', '', `联系人`, purchaseData.buyer.contact],
      [`联系电话`, purchaseData.seller.phone, '', '', '', '', `联系电话`, purchaseData.buyer.phone],
      [`地址`, purchaseData.seller.address, '', '', '', '', `地址`, purchaseData.buyer.address],
      [
        '图片',
        '维那型号/客户编号',
        '工厂型号',
        '产品名称',
        '描述',
        '规格/CM',
        '外包装尺寸',
        '数量',
        '单位',
        '净重/毛重',
        '单价 (含税)',
        '总金额 (含税)',
      ],
      ...purchaseData.items.map((it) => [
        '',
        `${it.weina_code || it.code}\n${it.customer_code || ''}`,
        it.factory_code || '',
        it.name,
        it.description || it.detail_requirement || '',
        it.spec || it.specification || '',
        it.pack_size || it.package_size || '',
        it.qty,
        it.unit || '个',
        it.nw_gw || '',
        it.unit_price,
        it.qty * it.unit_price,
      ]),
      ['总计', '', '', '', '', '', '', totalQuantity.value, '', '', '', totalAmount.value],
      ['产品要求', purchaseData.product_requirement],
      ['包装要求', purchaseData.package_requirement],
      ['交货日期', purchaseData.delivery_date],
      ['交货地址', purchaseData.delivery_address],
      ['供应商收款名称', purchaseData.supplier_bank_name || purchaseData.seller.name, '', '', '', '', '收货联系人', purchaseData.receiver_contact],
      ['开发行及账号', purchaseData.supplier_bank_account, '', '', '', '', '联系电话', purchaseData.receiver_phone],
      ['付款方式', purchaseData.payment_method],
      ['备注', purchaseData.remarks || ''],
      ['合同条款：'],
      ...purchaseData.clauses.map((c) => [c]),
      [],
      [`卖方：${purchaseData.sign_seller.name || purchaseData.seller.name}`, '', '', '', '', '', `买方：${purchaseData.sign_buyer.name || purchaseData.buyer.name}`],
      ['单位名称(公章)：'],
      [`单位地址：${purchaseData.sign_seller.address || purchaseData.seller.address}`, '', '', '', '', '', `单位地址：${purchaseData.sign_buyer.address || purchaseData.buyer.address}`],
      [`联系人：${purchaseData.sign_seller.contact || purchaseData.seller.contact}`, '', '', '', '', '', `联系人：${purchaseData.sign_buyer.contact || purchaseData.buyer.contact}`],
      [`电话：${purchaseData.sign_seller.phone || purchaseData.seller.phone}`, '', '', '', '', '', `电话：${purchaseData.sign_buyer.phone || purchaseData.buyer.phone}`],
    ]

    const ws = XLSX.utils.aoa_to_sheet(wsData)

    ws['!cols'] = [
      { wch: 8 },  // 图片
      { wch: 16 }, // 维那型号/客户编号
      { wch: 14 }, // 工厂型号
      { wch: 18 }, // 产品名称
      { wch: 22 }, // 描述
      { wch: 12 }, // 规格
      { wch: 14 }, // 外包装尺寸
      { wch: 8 },  // 数量
      { wch: 6 },  // 单位
      { wch: 12 }, // 净重/毛重
      { wch: 12 }, // 单价
      { wch: 14 }, // 总金额
    ]

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '采购合同')
    XLSX.writeFile(wb, `Purchase_Contract_${purchaseData.pi_no}.xlsx`)
    ElMessage.success('采购合同 Excel 导出成功！')
  } catch (err) {
    ElMessage.error('导出失败：' + (err as Error).message)
  }
}

defineExpose({ handleExportExcel, handlePrint })
</script>

<style scoped>
.purchase-sheet-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  background-color: #f1f5f9;
}
.purchase-sheet {
  width: 210mm;
  min-height: 297mm;
  padding: 12mm 15mm;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
  font-family: 'SimSun', 'STSong', serif;
  color: #000000;
  position: relative;
}

/* 顶部绿线与大标题 */
.top-green-line {
  height: 3px;
  background-color: #10b981;
  margin-bottom: 8px;
}
.company-title {
  text-align: center;
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 1px;
  margin: 0 0 8px 0;
  color: #000000;
}

/* 合同类型黑框条 */
.contract-header-bar {
  background-color: #4b5563;
  color: #ffffff;
  text-align: center;
  padding: 4px 0;
  font-size: 15px;
  font-weight: bold;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

/* 元信息行 */
.contract-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  margin-bottom: 6px;
}
.formula-hint {
  font-size: 11px;
  color: #374151;
}
.po-no {
  font-weight: bold;
}

/* 买卖双方信息表格 */
.party-info-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #000000;
  margin-bottom: 8px;
}
.party-info-table td {
  border: 1px solid #000000;
  padding: 4px 6px;
  font-size: 12px;
}
.seal-prompt-row td {
  background-color: #f9fafb;
  font-size: 12px;
}
.label-col {
  width: 12%;
  text-align: center;
  font-weight: bold;
  background-color: #ffffff;
}
.val-col {
  width: 38%;
}
.border-right {
  border-right: 1px solid #000000 !important;
}

/* 明细表格 */
.purchase-items-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #000000;
}
.purchase-items-table th,
.purchase-items-table td {
  border: 1px solid #000000;
  padding: 4px;
  font-size: 11px;
  line-height: 1.3;
}
.purchase-items-table th {
  background-color: #ffffff;
  font-weight: bold;
  text-align: center;
}
.item-img {
  width: 36px;
  height: 36px;
  object-fit: cover;
}
.total-row td {
  border-top: 2px solid #000000;
  padding: 6px 4px;
}

/* 约定事项表格 */
.terms-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #000000;
}
.terms-table td {
  border: 1px solid #000000;
  padding: 4px 6px;
  font-size: 11px;
}
.terms-label {
  width: 15%;
  font-weight: bold;
  background-color: #ffffff;
}
.terms-val {
  font-size: 11px;
}

/* 合同条款 */
.clauses-wrapper {
  border-top: 1px solid #10b981;
  border-bottom: 1px solid #10b981;
  padding: 6px 0;
  font-size: 11px;
  line-height: 1.5;
}
.clauses-title-bar {
  margin-bottom: 2px;
}
.clauses-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}
.clauses-list li {
  margin-bottom: 2px;
}

/* 底部签章区方框 */
.signature-boxes-container {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.sig-box {
  width: 48%;
  border: 1px solid #000000;
  padding: 8px 10px;
  min-height: 110px;
  box-sizing: border-box;
  position: relative;
  font-size: 12px;
}
.sig-title {
  margin-bottom: 8px;
}
.sig-line {
  margin-bottom: 4px;
}
.stamp-overlay {
  position: absolute;
  right: 12px;
  bottom: 8px;
  width: 85px;
  height: 85px;
  pointer-events: none;
  opacity: 0.85;
}
.stamp-overlay img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 工具辅助类 */
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-left { text-align: left; }
.font-bold { font-weight: bold; }
.text-danger { color: #dc2626; }
.text-gray { color: #9ca3af; }
.text-lg { font-size: 14px; }
</style>
