<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑收款记录' : '添加收款记录'"
    width="550px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="PI单" prop="pi_id">
        <el-select
          v-model="form.pi_id"
          filterable
          remote
          reserve-keyword
          placeholder="输入PI单号搜索"
          :remote-method="searchPi"
          :loading="piLoading"
          style="width: 100%"
          @change="onPiChange"
        >
          <el-option
            v-for="item in piList"
            :key="item.id"
            :label="item.pi_no"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="客户">
        <span>{{ form.customer_name || '-' }}</span>
      </el-form-item>

      <el-form-item label="付款日期" prop="payment_date">
        <el-date-picker
          v-model="form.payment_date"
          type="date"
          placeholder="选择日期"
          style="width: 100%"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="实收金额" prop="actual_amount">
        <el-input-number
          v-model="form.actual_amount"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="手续费">
        <el-input-number
          v-model="form.handling_fee"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="付款方式" prop="payment_method">
        <el-select v-model="form.payment_method" style="width: 100%">
          <el-option label="银行转账" value="bank_transfer" />
          <el-option label="现金" value="cash" />
          <el-option label="支票" value="check" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注信息" />
      </el-form-item>

      <el-form-item label="水单图片">
        <WaterBillUploader v-model="form.water_image" />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="onClose">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">
          确认
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import type { ArCustomerPayment } from '@/types/payment'
import { apiUrl } from '@/api/base'
import { orderSummaryApi } from '@/api/orderSummary'
import { isFormalOrderStatus } from '@/utils/formalRecord'
import WaterBillUploader from './WaterBillUploader.vue'

interface PiListItem {
  id: number
  pi_no: string
  customer_id: number
  customer_name?: string
  dept_id?: string
  total_amount?: number
}

const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const piLoading = ref(false)
const piList = ref<PiListItem[]>([])

const form = reactive({
  pi_id: null as number | null,
  customer_id: null as number | null,
  dept_id: 'S',
  amount: 0,
  customer_name: '',
  payment_date: new Date().toISOString().split('T')[0],
  actual_amount: 0,
  handling_fee: 0,
  payment_method: 'bank_transfer',
  remark: '',
  water_image: ''
})

const rules: FormRules = {
  pi_id: [{ required: true, message: '请选择PI单', trigger: 'change' }],
  payment_date: [{ required: true, message: '请选择付款日期', trigger: 'change' }],
  actual_amount: [{ required: true, message: '请输入实收金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择付款方式', trigger: 'change' }]
}

const isEdit = computed(() => editingId.value !== null)

const emit = defineEmits<{
  (e: 'success'): void
}>()

let searchPiTimer: ReturnType<typeof setTimeout> | null = null

async function searchPi(query: string) {
  if (searchPiTimer) {
    clearTimeout(searchPiTimer)
  }

  if (!query) {
    piList.value = []
    return
  }

  searchPiTimer = setTimeout(async () => {
    piLoading.value = true
    try {
      const res = await orderSummaryApi.getOrders({
        page: 1,
        page_size: 100,
        search: query,
      })
      piList.value = (res.data.code === 200 ? res.data.data.list : [])
        .filter(item => isFormalOrderStatus(item.status))
        .map(item => ({
          id: item.id,
          pi_no: item.pi_no,
          customer_id: item.customer_id,
          customer_name: item.customer_name,
          total_amount: item.total_amount,
        }))
    } catch {
      ElMessage.error('查询正式PI单失败')
    } finally {
      piLoading.value = false
    }
  }, 300)
}

function onPiChange(piId: number) {
  const selected = piList.value.find(item => item.id === piId)
  if (selected) {
    form.customer_id = selected.customer_id || null
    form.dept_id = selected.dept_id || 'S'
    form.amount = selected.total_amount || 0
    form.customer_name = selected.customer_name || ''
  }
}

async function onSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!form.pi_id) return

    submitting.value = true
    try {
      const url = isEdit.value
        ? apiUrl(`/api/payments/receivables/${editingId.value}`)
        : apiUrl('/api/payments/receivables')

      const method = isEdit.value ? 'PUT' : 'POST'

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dept_id: form.dept_id || 'S',
          pi_id: form.pi_id,
          customer_id: form.customer_id,
          amount: form.amount,
          actual_amount: form.actual_amount,
          handling_fee: form.handling_fee || undefined,
          payment_date: form.payment_date,
          payment_method: form.payment_method || undefined,
          remark: form.remark || undefined,
          water_image: form.water_image || undefined
        })
      })

      const data = await res.json()
      if (res.ok && data.code === 200) {
        ElMessage.success(isEdit.value ? '编辑成功' : '添加成功')
        emit('success')
        onClose()
      } else {
        ElMessage.error(data.message || '操作失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function onClose() {
  formRef.value?.resetFields()
  form.pi_id = null
  form.customer_id = null
  form.dept_id = 'S'
  form.amount = 0
  form.customer_name = ''
  form.payment_date = new Date().toISOString().split('T')[0]
  form.actual_amount = 0
  form.handling_fee = 0
  form.payment_method = 'bank_transfer'
  form.remark = ''
  form.water_image = ''
  editingId.value = null
  piList.value = []
  visible.value = false
}

function open(payment?: ArCustomerPayment) {
  if (payment) {
    editingId.value = payment.id
    form.pi_id = payment.pi_id
    form.customer_id = (payment as any).customer_id || null
    form.dept_id = (payment as any).dept_id || 'S'
    form.amount = (payment as any).amount || 0
    form.customer_name = payment.customer_name || ''
    form.payment_date = payment.payment_date
    form.actual_amount = payment.actual_amount
    form.handling_fee = payment.handling_fee || 0
    form.payment_method = payment.payment_method || 'bank_transfer'
    form.remark = payment.remark || ''
    form.water_image = payment.water_image || ''
    piList.value = [{ id: payment.pi_id, pi_no: payment.pi_no || '', customer_id: (payment as any).customer_id || 0, customer_name: payment.customer_name }]
  } else {
    editingId.value = null
  }
  visible.value = true
}

defineExpose({ open })
</script>

<style scoped>
</style>
