<template>
  <div class="export-edit-form-body">
    <!-- 1. 基础信息与买卖双方 -->
    <div class="edit-section">
      <div class="section-title basic-title">
        基础信息与买卖双方 (Header & Party Information)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="公司抬头名称">
              <el-input v-model="formData.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="PI 单号">
              <el-input v-model="formData.pi_no" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="订单日期">
              <el-input v-model="formData.order_date" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="目的港 (Final Destination)">
              <el-input v-model="formData.buyer.final_destination" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 买卖双方 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">BUYER 买方信息</div>
              <el-form-item label="买方名称 (TO)">
                <el-input v-model="formData.buyer.name" />
              </el-form-item>
              <el-form-item label="买方电话 (Tel)">
                <el-input v-model="formData.buyer.tel" />
              </el-form-item>
              <el-form-item label="买方地址 (Address)">
                <el-input v-model="formData.buyer.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>

          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">SELLER 卖方信息</div>
              <el-form-item label="联系人 (Contact)">
                <el-input v-model="formData.seller.contact" />
              </el-form-item>
              <el-form-item label="电话/WhatsApp">
                <el-input v-model="formData.seller.tel_whatsapp" />
              </el-form-item>
              <el-form-item label="卖方地址 (Address)">
                <el-input v-model="formData.seller.address" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="交货工期 (Delivery date)">
                <el-input v-model="formData.seller.delivery_date" />
              </el-form-item>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 2. 产品清单与费用明细 -->
    <div class="edit-section mt-4">
      <div class="section-title items-title">
        产品明细与费用修正 (Items & Additional Benefits)
      </div>
      <div class="section-body">
        <el-table :data="formData.items" border size="small" style="width: 100%">
          <el-table-column prop="name" label="品名 (NAME)" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="code" label="编号 (CODE)" width="110">
            <template #default="{ row }">
              <el-input v-model="row.code" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="description" label="产品描述 (Description)" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.description" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="specification" label="规格 (Specification)" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.specification" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="pcs_ctn" label="装箱规格" width="100">
            <template #default="{ row }">
              <el-input v-model="row.pcs_ctn" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="color" label="颜色" width="100">
            <template #default="{ row }">
              <el-input v-model="row.color" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="qty" label="数量 (QTY)" width="110">
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

        <!-- 附加优惠 -->
        <el-row :gutter="16" class="mt-3">
          <el-col :span="12">
            <el-form-item label="附加优惠标签 (Additional Benefits Label)">
              <el-input v-model="formData.additional_benefits.label" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="附加优惠金额 ($)">
              <el-input-number v-model="formData.additional_benefits.amount" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 3. 备注条款与银行信息 -->
    <div class="edit-section mt-4">
      <div class="section-title remarks-title">
        条款备注与银行资料 (Remarks & Bank Information)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="remark-header-bar">
                <div class="sub-card-title mb-0">Remark 备注条款 (多行每行一条)</div>
                <!-- 备注字号调控操作工具栏 -->
                <div class="remark-font-size-control">
                  <span class="control-label">字号设置:</span>
                  <el-button
                    type="default"
                    size="small"
                    title="缩小字号"
                    :disabled="(formData.remark_font_size || 11) <= 9"
                    @click="adjustRemarkFontSize(-1)"
                  >
                    A-
                  </el-button>
                  <span class="current-size-display">{{ formData.remark_font_size || 11 }}px</span>
                  <el-button
                    type="default"
                    size="small"
                    title="放大字号"
                    :disabled="(formData.remark_font_size || 11) >= 24"
                    @click="adjustRemarkFontSize(1)"
                  >
                    A+
                  </el-button>
                  <el-radio-group
                    v-model="formData.remark_font_size"
                    size="small"
                    class="ms-2"
                  >
                    <el-radio-button
                      v-for="size in [10, 11, 12, 13, 14, 16]"
                      :key="size"
                      :value="size"
                    >
                      {{ size }}
                    </el-radio-button>
                  </el-radio-group>
                </div>
              </div>
              <el-input
                v-model="remarkText"
                type="textarea"
                :rows="8"
                placeholder="请输入备注条款..."
                @blur="onRemarkBlur"
              />
            </div>
          </el-col>
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">BANK INFORMATION 银行账号</div>
              <el-form-item label="Beneficiary (收款人)">
                <el-input v-model="formData.bank.beneficiary" />
              </el-form-item>
              <el-form-item label="BANK NAME (开户行)">
                <el-input v-model="formData.bank.bank_name" />
              </el-form-item>
              <el-form-item label="BANK ADDRESS (银行地址)">
                <el-input v-model="formData.bank.bank_address" />
              </el-form-item>
              <el-form-item label="SWIFT BIC">
                <el-input v-model="formData.bank.swift_bic" />
              </el-form-item>
              <el-form-item label="Tel & Fax">
                <el-input v-model="formData.bank.tel_fax" />
              </el-form-item>
              <el-form-item label="Account No (账号)">
                <el-input v-model="formData.bank.account_no" />
              </el-form-item>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 4. 签章与印章管理 -->
    <div class="edit-section mt-4">
      <div class="section-title stamp-title">
        电子签章配置 (Signatures & Seal Management)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">卖方章印 (The Seller's Stamp)</div>
              <el-form-item label="显示卖方章印">
                <el-switch v-model="formData.seller_stamp.show_stamp" />
              </el-form-item>
              <el-form-item label="持久化公章 (backend/data/signatures)">
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

          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">买方章印 (The Buyer's Stamp)</div>
              <el-form-item label="显示买方章印">
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
 * @fileoverview PI 形式发票编辑子表单组件 (PiEditForm.vue)
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

const emit = defineEmits<{
  'update:modelValue': [val: any]
}>()

const formData = props.modelValue

// 初始化确保 remark_font_size 具备默认数值 (默认 11px)
if (formData && formData.remark_font_size === undefined) {
  formData.remark_font_size = 11
}

/**
 * 调整 Remark 备注字号大小 (单位: px)
 * @param delta 字号增减步长 (+1 或 -1)
 */
function adjustRemarkFontSize(delta: number): void {
  if (!formData) return
  const current = formData.remark_font_size || 11
  const next = Math.min(24, Math.max(9, current + delta))
  formData.remark_font_size = next
}

/**
 * 直接设置 Remark 备注目标字号大小 (单位: px)
 * @param size 目标字号数值 (9-24)
 */
function setRemarkFontSize(size: number): void {
  if (!formData) return
  formData.remark_font_size = Math.min(24, Math.max(9, size))
}

const remarkText = ref(Array.isArray(formData?.remarks) ? formData.remarks.join('\n\n') : '')

watch(
  () => formData?.remarks,
  (newRemarks) => {
    if (Array.isArray(newRemarks)) {
      remarkText.value = newRemarks.join('\n\n')
    }
  },
  { deep: true }
)

function onRemarkBlur() {
  if (formData) {
    formData.remarks = remarkText.value.split(/\n\n+/).filter(Boolean)
  }
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
.stamp-title { color: #7c3aed; }
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
.remark-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
.remark-font-size-control {
  display: flex;
  align-items: center;
  gap: 6px;
}
.control-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}
.current-size-display {
  font-size: 12px;
  font-weight: 600;
  color: #0284c7;
  min-width: 32px;
  text-align: center;
}
.mb-0 {
  margin-bottom: 0 !important;
}
.ms-2 {
  margin-left: 8px;
}
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
</style>
