<template>
  <el-dialog
    v-model="visible"
    :title="`添加付款 - ${order?.pi_no || ''}`"
    width="500px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="订单号">
        <span>{{ order?.pi_no }}</span>
      </el-form-item>
      
      <el-form-item label="客户">
        <span>{{ order?.customer_name }}</span>
      </el-form-item>
      
      <el-form-item label="订单总额">
        <span class="amount">{{ formatAmount(order?.total_amount || 0) }} USD</span>
      </el-form-item>
      
      <el-form-item label="已付金额">
        <span class="amount success">{{ formatAmount(order?.paid_amount || 0) }} USD</span>
      </el-form-item>
      
      <el-form-item label="未付金额">
        <span class="amount warning">{{ formatAmount(order?.unpaid_amount || 0) }} USD</span>
      </el-form-item>
      
      <el-divider />
      
      <el-form-item label="付款类型" prop="stage_type">
        <el-select v-model="form.stage_type" style="width: 100%">
          <el-option label="预付款 (Prepayment)" value="prepayment" />
          <el-option label="尾款 (Balance)" value="balance" />
          <el-option label="全款 (Full Payment)" value="full" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="付款金额" prop="amount">
        <el-input-number
          v-model="form.amount"
          :min="0"
          :max="order?.unpaid_amount || 999999"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="付款日期" prop="paid_date">
        <el-date-picker
          v-model="form.paid_date"
          type="date"
          placeholder="选择日期"
          style="width: 100%"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="付款方式" prop="payment_method">
        <el-select v-model="form.payment_method" placeholder="请选择付款方式" style="width: 100%">
          <el-option label="银行转账" value="银行转账" />
          <el-option label="现金" value="现金" />
          <el-option label="支票" value="支票" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>

      <el-form-item label="手续费">
        <el-input-number
          v-model="form.handling_fee"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="onClose">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">
          确认付款
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import type { OrderListItem } from '@/types/orderSummary'
import { apiUrl } from '@/api/base'
import { PI } from '@/api/endpoints'

const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const order = ref<OrderListItem | null>(null)

const form = reactive({
  stage_type: 'prepayment',
  amount: 0,
  paid_date: new Date().toISOString().split('T')[0],
  payment_method: '',
  handling_fee: 0,
  remark: ''
})

const rules: FormRules = {
  stage_type: [{ required: true, message: '请选择付款类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入付款金额', trigger: 'blur' }],
  paid_date: [{ required: true, message: '请选择付款日期', trigger: 'change' }]
}

const emit = defineEmits<{
  (e: 'success'): void
}>()

function formatAmount(amount: number): string {
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function onSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!order.value?.id) return
    
    submitting.value = true
    try {
      const res = await fetch(apiUrl(`/api/pi/${order.value.id}/payments`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stage_type: form.stage_type,
          amount: form.amount,
          paid_date: form.paid_date,
          payment_method: form.payment_method || undefined,
          handling_fee: form.handling_fee || 0,
          remark: form.remark || undefined
        })
      })
      
      if (res.ok) {
        ElMessage.success('付款记录添加成功')
        emit('success')
        onClose()
      } else {
        const err = await res.json()
        ElMessage.error(err.message || '添加失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '添加付款失败')
    } finally {
      submitting.value = false
    }
  })
}

function onClose() {
  formRef.value?.resetFields()
  form.stage_type = 'prepayment'
  form.amount = 0
  form.paid_date = new Date().toISOString().split('T')[0]
  form.payment_method = ''
  form.handling_fee = 0
  form.remark = ''
  visible.value = false
}

function open(orderData: OrderListItem) {
  order.value = orderData
  form.amount = orderData.unpaid_amount || 0
  visible.value = true
}

defineExpose({ open })
</script>

<style scoped>
.amount {
  font-weight: 600;
}
.amount.success {
  color: #67c23a;
}
.amount.warning {
  color: #e6a23c;
}
</style>
