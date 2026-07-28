<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="92vw"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
    class="export-edit-modal-wrapper"
  >
    <!-- 多子表单组件动态切换区域 -->
    <component
      :is="activeFormComponent"
      v-model="formData"
      :available-signatures="availableSignatures"
    />

    <template #footer>
      <div class="modal-footer">
        <el-button @click="onCancel">取消</el-button>
        <el-button type="primary" @click="onConfirmSave">
          保存并更新预览
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @fileoverview 通用导出编辑弹窗组件 (ExportEditModal.vue)
 * 采用多子表单组件架构 (Multi-subform Strategy Architecture)，
 * 根据传入的 docType 动态挂载对应的单据编辑表单（PiEditForm / CiEditForm / PlEditForm / PurchaseEditForm）。
 */

import { computed, ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { apiUrl } from '@/api/base'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'

import PiEditForm from './forms/PiEditForm.vue'
import CiEditForm from './forms/CiEditForm.vue'
import PlEditForm from './forms/PlEditForm.vue'
import PurchaseEditForm from './forms/PurchaseEditForm.vue'

const store = useOrderSummaryStore()

interface SignatureItem {
  filename: string
  url: string
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    docType: 'pi' | 'ci' | 'pl' | 'purchase'
  }>(),
  {
    modelValue: false,
    docType: 'pi',
  }
)

const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  save: [data: any]
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

/** 动态匹配激活对应的子编辑表单组件 */
const activeFormComponent = computed(() => {
  switch (props.docType) {
    case 'ci':
      return CiEditForm
    case 'pl':
      return PlEditForm
    case 'purchase':
      return PurchaseEditForm
    case 'pi':
    default:
      return PiEditForm
  }
})

const dialogTitle = computed(() => {
  switch (props.docType) {
    case 'pi':
      return '编辑单据内容 - PROFORMA INVOICE (PI 形式发票)'
    case 'ci':
      return '编辑单据内容 - COMMERCIAL INVOICE (CI 商业发票)'
    case 'pl':
      return '编辑单据内容 - PACKING LIST (PL 装箱单)'
    case 'purchase':
      return '编辑单据内容 - PURCHASE INVOICE (采购合同)'
    default:
      return '编辑单据内容'
  }
})

/** 持久化签章文件列表 */
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
    console.warn('获取持久化签章列表失败', err)
  }
})

/** 响应式单据大表单模型 */
const formData = reactive<any>({
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
      description: '/',
      specification: '/',
      pcs_ctn: '/',
      color: '',
      qty: 2,
      unit_price: 5.0,
    },
    {
      name: 'Accessories',
      code: '',
      description: '',
      specification: '',
      pcs_ctn: '',
      color: '',
      qty: 10,
      unit_price: 65.0,
    },
  ],
  additional_benefits: {
    label: 'Additional benefits',
    amount: 35.0,
  },
  remarks: [
    'Should be have labels with a crossed knife to each box with pillows.\nThe label thread on the back of the seat cushion.',
    '1.Price Terms:FOB',
    '2.Payment Terms: T/T 10% deposit ,The 90% balance according to the BL.',
    '3. SHIPPING MARKS ARE BUYER\'S OPTION',
    'Warranty Time: 13 months after the shiping date',
  ],
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
  // CI 专属
  ci_loading_port: 'Ningbo, China',
  ci_bl_no: '',
  ci_carriage: 'BY SEA / FOB NINGBO',
  // PL 专属
  pl_info: {
    total_cartons: 970,
    total_gw_kg: 18500,
    total_nw_kg: 17200,
    total_cbm: 68.5,
    shipping_marks: 'N/M\nMADE IN CHINA',
  },
})

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      const savedData = store.loadExportDocData()
      if (savedData) {
        Object.assign(formData, JSON.parse(JSON.stringify(savedData)))
      } else if (store.currentOrder) {
        if (store.currentOrder.pi_no) formData.pi_no = store.currentOrder.pi_no
        if (store.currentOrder.created_at) formData.order_date = store.currentOrder.created_at
        if (store.currentOrder.customer_name) formData.buyer.name = store.currentOrder.customer_name

        if (store.detailItems && store.detailItems.length > 0) {
          if (store.detailItems[0].order_date) {
            formData.order_date = store.detailItems[0].order_date
          }
          formData.items = store.detailItems.map((item) => ({
            name: item.customer_model || item.product_name || '未命名产品',
            code: item.factory_code || item.product_code || '',
            description: item.product_acquires || item.product_name || item.product_name_en || '/',
            specification: item.product_feature || 'Standard',
            pcs_ctn: item.pack_spec || item.packaging || '1pcs/1ctn',
            color: item.product_color || '',
            qty: item.quantity || 1,
            unit_price: item.unit_price || 0,
          }))
        }
      }
    }
  },
  { immediate: true }
)

function onCancel() {
  dialogVisible.value = false
}

function onConfirmSave() {
  const savedPayload = JSON.parse(JSON.stringify(formData))
  store.setExportDocData(savedPayload)
  ElMessage.success('单据数据修改成功！')
  emit('save', savedPayload)
  dialogVisible.value = false
}
</script>

<style scoped>
.export-edit-modal-wrapper :deep(.el-dialog__body) {
  padding: 12px 20px;
}
.export-edit-form-body {
  max-height: 76vh;
  overflow-y: auto;
  padding-right: 4px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
