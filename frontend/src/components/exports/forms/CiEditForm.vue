<template>
  <div class="export-edit-form-body">
    <!-- 1. CI 基础发票与报关信息 -->
    <div class="edit-section">
      <div class="section-title basic-title">
        CI 商业发票基础信息 (Commercial Invoice Meta)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="公司抬头名称">
              <el-input v-model="formData.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="发票编号 (Invoice No.)">
              <el-input v-model="formData.pi_no" placeholder="如 CI20260521" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="开票日期 (Invoice Date)">
              <el-input v-model="formData.order_date" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="目的港 (Port of Discharge)">
              <el-input v-model="formData.buyer.final_destination" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 提单与运输参数 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="8">
            <el-form-item label="起运港 (Port of Loading)">
              <el-input v-model="formData.ci_loading_port" placeholder="如 Ningbo, China" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="提单号 (B/L No.)">
              <el-input v-model="formData.ci_bl_no" placeholder="如 NGB20260521001" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="运输方式 (Terms / Carriage)">
              <el-input v-model="formData.ci_carriage" placeholder="如 BY SEA / FOB NINGBO" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 买卖双方 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">BUYER / CONSIGNEE 买方收货人</div>
              <el-form-item label="买方名称">
                <el-input v-model="formData.buyer.name" />
              </el-form-item>
              <el-form-item label="电话">
                <el-input v-model="formData.buyer.tel" />
              </el-form-item>
              <el-form-item label="买方地址">
                <el-input v-model="formData.buyer.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>

          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">SELLER / EXPORTER 卖方发货人</div>
              <el-form-item label="联系人">
                <el-input v-model="formData.seller.contact" />
              </el-form-item>
              <el-form-item label="电话/WhatsApp">
                <el-input v-model="formData.seller.tel_whatsapp" />
              </el-form-item>
              <el-form-item label="卖方地址">
                <el-input v-model="formData.seller.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 2. 产品清册与开票金额明细 -->
    <div class="edit-section mt-4">
      <div class="section-title items-title">
        开票产品与报关金额 (Invoice Line Items & Amounts)
      </div>
      <div class="section-body">
        <el-table :data="formData.items" border size="small" style="width: 100%">
          <el-table-column prop="name" label="英文品名" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="code" label="型号/编号" width="120">
            <template #default="{ row }">
              <el-input v-model="row.code" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="description" label="规格描述" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.description" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="qty" label="开票数量" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.qty" :min="1" size="small" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column prop="unit_price" label="单价 ($)" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :precision="2" :step="0.1" size="small" style="width: 100%" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 3. CI 专属备注声明与签章 -->
    <div class="edit-section mt-4">
      <div class="section-title remarks-title">
        发票备注声明与公章配置 (Remarks & Declaration)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="14">
            <el-form-item label="CI 声明与条款备注 (多行每行一条)">
              <el-input v-model="remarkText" type="textarea" :rows="6" @blur="onRemarkBlur" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <div class="sub-card-box">
              <div class="sub-card-title">卖方公司盖章 (Seller Stamp)</div>
              <el-form-item label="显示盖章">
                <el-switch v-model="formData.seller_stamp.show_stamp" />
              </el-form-item>
              <el-form-item label="公章印件">
                <el-select v-model="formData.seller_stamp.stamp_url" style="width: 100%">
                  <el-option
                    v-for="st in availableSignatures"
                    :key="st.url"
                    :label="st.filename"
                    :value="st.url"
                  />
                </el-select>
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
 * @fileoverview CI 商业发票编辑子表单组件 (CiEditForm.vue)
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

if (!formData.ci_loading_port) formData.ci_loading_port = 'Ningbo, China'
if (!formData.ci_bl_no) formData.ci_bl_no = ''
if (!formData.ci_carriage) formData.ci_carriage = 'BY SEA / FOB NINGBO'

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
