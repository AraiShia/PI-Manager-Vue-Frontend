<template>
  <div class="export-edit-form-body">
    <!-- 1. PL 装箱单基础与装运信息 -->
    <div class="edit-section">
      <div class="section-title basic-title">
        PL 装箱单基础信息 (Packing List Meta)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="公司抬头名称">
              <el-input v-model="formData.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="装箱单号 (PL No.)">
              <el-input v-model="formData.pi_no" placeholder="如 PL20260521" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="发货日期 (Date)">
              <el-input v-model="formData.order_date" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="目的港 (Destination)">
              <el-input v-model="formData.buyer.final_destination" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 重量与体积汇总统计 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="6">
            <el-form-item label="总箱数 (Total Cartons)">
              <el-input-number v-model="plTotalCartons" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="总毛重 (Total G.W. kg)">
              <el-input-number v-model="plTotalGw" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="总净重 (Total N.W. kg)">
              <el-input-number v-model="plTotalNw" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="总体积 (Total CBM)">
              <el-input-number v-model="plTotalCbm" :precision="3" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 2. 产品装箱规格列表 -->
    <div class="edit-section mt-4">
      <div class="section-title items-title">
        产品装箱规格与件数 (Package Specifications & Quantities)
      </div>
      <div class="section-body">
        <el-table :data="formData.items" border size="small" style="width: 100%">
          <el-table-column prop="name" label="品名" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="code" label="型号代码" width="110">
            <template #default="{ row }">
              <el-input v-model="row.code" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="specification" label="规格说明" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.specification" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="pcs_ctn" label="装箱规格 (pcs/ctn)" width="120">
            <template #default="{ row }">
              <el-input v-model="row.pcs_ctn" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="qty" label="总件数 (PCS)" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.qty" :min="1" size="small" style="width: 100%" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 3. 唛头 Shipping Marks 与盖章 -->
    <div class="edit-section mt-4">
      <div class="section-title remarks-title">
        唛头信息与电子印章 (Shipping Marks & Stamp)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="14">
            <el-form-item label="外箱唛头 (Shipping Marks)">
              <el-input v-model="shippingMarksText" type="textarea" :rows="5" placeholder="如：\nN/M\nITEM NO: WM-8012\nQTY: 970 PCS\nMADE IN CHINA" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <div class="sub-card-box">
              <div class="sub-card-title">发货方公章 (Seller Stamp)</div>
              <el-form-item label="显示公章">
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
            </div>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview PL 装箱单编辑子表单组件 (PlEditForm.vue)
 */
import { ref, computed } from 'vue'

interface SignatureItem {
  filename: string
  url: string
}

const props = defineProps<{
  modelValue: any
  availableSignatures?: SignatureItem[]
}>()

const formData = props.modelValue

if (!formData.pl_info) {
  formData.pl_info = {
    total_cartons: 970,
    total_gw_kg: 18500,
    total_nw_kg: 17200,
    total_cbm: 68.5,
    shipping_marks: 'N/M\nMADE IN CHINA',
  }
}

const plTotalCartons = computed({
  get: () => formData.pl_info.total_cartons || 0,
  set: (val) => { formData.pl_info.total_cartons = val },
})
const plTotalGw = computed({
  get: () => formData.pl_info.total_gw_kg || 0,
  set: (val) => { formData.pl_info.total_gw_kg = val },
})
const plTotalNw = computed({
  get: () => formData.pl_info.total_nw_kg || 0,
  set: (val) => { formData.pl_info.total_nw_kg = val },
})
const plTotalCbm = computed({
  get: () => formData.pl_info.total_cbm || 0,
  set: (val) => { formData.pl_info.total_cbm = val },
})

const shippingMarksText = computed({
  get: () => formData.pl_info.shipping_marks || '',
  set: (val) => { formData.pl_info.shipping_marks = val },
})
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
