<template>
  <div class="export-edit-form-body">
    <!-- 1. 采购合同主体信息 -->
    <div class="edit-section">
      <div class="section-title basic-title">
        采购合同基础信息 (Purchase Order Meta)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="采购主体 (买方)">
              <el-input v-model="formData.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="采购合同编号">
              <el-input v-model="formData.pi_no" placeholder="如 PO20260521" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="签订日期">
              <el-input v-model="formData.order_date" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="交货期限 (Delivery Deadline)">
              <el-input v-model="formData.seller.delivery_date" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 供方与需方 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">需方信息 (Buyer / Purchaser)</div>
              <el-form-item label="需方名称">
                <el-input v-model="formData.buyer.name" />
              </el-form-item>
              <el-form-item label="联系电话">
                <el-input v-model="formData.buyer.tel" />
              </el-form-item>
              <el-form-item label="需方地址">
                <el-input v-model="formData.buyer.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>

          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">供方/工厂信息 (Supplier / Factory)</div>
              <el-form-item label="供方联系人">
                <el-input v-model="formData.seller.contact" />
              </el-form-item>
              <el-form-item label="联系电话">
                <el-input v-model="formData.seller.tel_whatsapp" />
              </el-form-item>
              <el-form-item label="工厂/供方地址">
                <el-input v-model="formData.seller.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 2. 采购产品清单与单价金额 -->
    <div class="edit-section mt-4">
      <div class="section-title items-title">
        采购产品清单与结算金额 (Procurement Items & Pricing)
      </div>
      <div class="section-body">
        <el-table :data="formData.items" border size="small" style="width: 100%">
          <el-table-column prop="name" label="产品名称" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="code" label="工厂编号" width="110">
            <template #default="{ row }">
              <el-input v-model="row.code" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="specification" label="规格要求" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.specification" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="color" label="颜色" width="100">
            <template #default="{ row }">
              <el-input v-model="row.color" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="qty" label="采购数量" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.qty" :min="1" size="small" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column prop="unit_price" label="采购单价 (￥/$)" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :precision="2" :step="0.1" size="small" style="width: 100%" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 3. 采购条款与盖章控制 -->
    <div class="edit-section mt-4">
      <div class="section-title remarks-title">
        采购合同条款与签署盖章 (Terms & Contract Seals)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同约束条款 (多行每行一条)">
              <el-input v-model="remarkText" type="textarea" :rows="7" @blur="onRemarkBlur" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">双方印章与签字控制 (Seals & Signatures)</div>
              <el-form-item label="需方盖章">
                <el-switch v-model="formData.seller_stamp.show_stamp" />
              </el-form-item>
              <el-form-item label="选定公章印件">
                <el-select v-model="formData.seller_stamp.stamp_url" style="width: 100%">
                  <el-option
                    v-for="st in availableSignatures"
                    :key="st.url"
                    :label="st.filename"
                    :value="st.url"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="供方盖章">
                <el-switch v-model="formData.buyer_stamp.show_stamp" />
              </el-form-item>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview Purchase 采购合同编辑子表单组件 (PurchaseEditForm.vue)
 */
import { ref, watch } from 'vue'

interface SignatureItem {
  filename: string
  url: string
}

const props = defineProps<{
  modelValue: any
  availableSignatures?: SignatureItem[]
}>()

const formData = props.modelValue

const remarkText = ref(Array.isArray(formData.remarks) ? formData.remarks.join('\n\n') : '')

watch(
  () => formData.remarks,
  (newRemarks) => {
    if (Array.isArray(newRemarks)) {
      remarkText.value = newRemarks.join('\n\n')
    }
  },
  { deep: true }
)

function onRemarkBlur() {
  formData.remarks = remarkText.value.split(/\n\n+/).filter(Boolean)
}
</script>

<style scoped>
.edit-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  padding-bottom: 8px;
  margin-bottom: 12px;
  border-bottom: 1px solid #cbd5e1;
  color: #1e293b;
}
.basic-title { color: #0284c7; }
.items-title { color: #059669; }
.remarks-title { color: #d97706; }
.sub-card-box {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
}
.sub-card-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}
.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
</style>
