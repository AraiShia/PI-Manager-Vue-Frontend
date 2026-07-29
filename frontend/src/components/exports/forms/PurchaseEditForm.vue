<template>
  <div class="export-edit-form-body">
    <!-- 1. 采购合同主体信息 -->
    <div class="edit-section">
      <div class="section-title basic-title">
        采购合同基础信息 (Purchase Contract Meta)
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
              <el-input v-model="formData.pi_no" placeholder="如 XLW2204171" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="编号计算公式规则">
              <el-input v-model="formData.po_no_formula" placeholder="供应商编号 + 维那编号..." />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="签订日期">
              <el-input v-model="formData.order_date" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 供方与需方 -->
        <el-row :gutter="16" class="mt-2">
          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">买方/采购商信息 (Buyer / Purchaser)</div>
              <el-form-item label="买方名称">
                <el-input v-model="formData.buyer.name" />
              </el-form-item>
              <el-form-item label="联系人">
                <el-input v-model="formData.buyer.contact" />
              </el-form-item>
              <el-form-item label="联系电话">
                <el-input v-model="formData.buyer.phone" />
              </el-form-item>
              <el-form-item label="单位地址">
                <el-input v-model="formData.buyer.address" type="textarea" :rows="2" />
              </el-form-item>
            </div>
          </el-col>

          <el-col :span="12">
            <div class="sub-card-box">
              <div class="sub-card-title">卖方/供应商信息 (Supplier / Factory)</div>
              <el-form-item label="供应商名称">
                <el-input v-model="formData.seller.name" />
              </el-form-item>
              <el-form-item label="联系人">
                <el-input v-model="formData.seller.contact" />
              </el-form-item>
              <el-form-item label="联系电话">
                <el-input v-model="formData.seller.phone" />
              </el-form-item>
              <el-form-item label="工厂地址">
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
          <el-table-column label="维那型号" width="110">
            <template #default="{ row }">
              <el-input v-model="row.weina_code" size="small" placeholder="维那型号" />
            </template>
          </el-table-column>
          <el-table-column label="客户编号 (红字)" width="120">
            <template #default="{ row }">
              <el-input v-model="row.customer_code" size="small" placeholder="客户编号" />
            </template>
          </el-table-column>
          <el-table-column label="工厂型号" width="110">
            <template #default="{ row }">
              <el-input v-model="row.factory_code" size="small" placeholder="工厂型号" />
            </template>
          </el-table-column>
          <el-table-column label="产品名称" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="描述" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.description" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="规格/CM" width="100">
            <template #default="{ row }">
              <el-input v-model="row.spec" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="外包装尺寸" width="110">
            <template #default="{ row }">
              <el-input v-model="row.pack_size" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="90">
            <template #default="{ row }">
              <el-input-number v-model="row.qty" :min="1" size="small" style="width: 100%" :controls="false" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="70">
            <template #default="{ row }">
              <el-input v-model="row.unit" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="净重/毛重" width="100">
            <template #default="{ row }">
              <el-input v-model="row.nw_gw" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="含税单价 (¥)" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :precision="2" :step="0.1" size="small" style="width: 100%" :controls="false" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 3. 约定事项与交付方式 -->
    <div class="edit-section mt-4">
      <div class="section-title terms-title">
        约定事项与交货方式 (Terms & Shipping Details)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品要求 (预览呈现红色警告)">
              <el-input v-model="formData.product_requirement" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装要求">
              <el-input v-model="formData.package_requirement" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="交货日期">
              <el-input v-model="formData.delivery_date" placeholder="如 2025/05/18日前" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="交货地址">
              <el-input v-model="formData.delivery_address" placeholder="送到买方指定仓库..." />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="收货联系人及电话">
              <el-input v-model="formData.receiver_contact" style="width: 48%" placeholder="联系人" />
              <el-input v-model="formData.receiver_phone" style="width: 48%; margin-left: 4%" placeholder="电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="供应商收款名称">
              <el-input v-model="formData.supplier_bank_name" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="开发行及账号 (开户行及账号)">
              <el-input v-model="formData.supplier_bank_account" placeholder="银行名称及账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="付款方式">
              <el-input v-model="formData.payment_method" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 4. 采购条款与盖章控制 -->
    <div class="edit-section mt-4">
      <div class="section-title remarks-title">
        采购合同条款与签署盖章 (Terms & Seals)
      </div>
      <div class="section-body">
        <el-row :gutter="16">
          <el-col :span="14">
            <el-form-item label="合同约束条款 (多行每行一条)">
              <el-input v-model="clausesText" type="textarea" :rows="6" @blur="onClausesBlur" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <div class="sub-card-box">
              <div class="sub-card-title">买卖双方公章控制</div>
              <el-form-item label="买方盖章 (显示于右方框)">
                <el-switch v-model="formData.buyer_stamp.show_stamp" />
              </el-form-item>
              <el-form-item label="买方所选公章">
                <el-select v-model="formData.buyer_stamp.stamp_url" style="width: 100%">
                  <el-option
                    v-for="st in availableSignatures"
                    :key="st.url"
                    :label="st.filename"
                    :value="st.url"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="卖方盖章 (显示于左方框)">
                <el-switch v-model="formData.seller_stamp.show_stamp" />
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
 * @fileoverview Purchase 采购合同编辑子表单组件 (与标准采购合同模板100%字段对齐)
 */
import { ref, watch, onMounted } from 'vue'

interface SignatureItem {
  filename: string
  url: string
}

const props = defineProps<{
  modelValue: any
  availableSignatures?: SignatureItem[]
}>()

const formData = props.modelValue

// 补全必要的数据字段默认值结构
onMounted(() => {
  if (!formData.po_no_formula) formData.po_no_formula = '供应商编号 + 维那编号 +采购日期 +序号'
  if (!formData.seller) formData.seller = { name: '', contact: '', phone: '', address: '' }
  if (!formData.buyer) formData.buyer = { name: '杭州维那贸易有限公司', contact: 'Jacky', phone: '18069766520', address: '' }
  if (!formData.product_requirement) formData.product_requirement = '无褶皱，清洁无线头，无银光笔笔痕，logo不能倾斜，正确区分青蛙托坐垫跟蝴蝶托坐垫'
  if (!formData.package_requirement) formData.package_requirement = '300磅五层双瓦纸箱，内加EPE打包方式'
  if (!formData.delivery_date) formData.delivery_date = '2025/05/18日前'
  if (!formData.delivery_address) formData.delivery_address = '送到买方指定仓库（卖方负责运输费用）'
  if (!formData.supplier_bank_name) formData.supplier_bank_name = formData.seller.name || '安吉大龙家具有限公司'
  if (!formData.supplier_bank_account) formData.supplier_bank_account = '湖州银行股份有限公司安吉支行    811265887000909'
  if (!formData.payment_method) formData.payment_method = '下好订单，卖方确认合同盖章后付预付款；预付款30%，剩余款装货前付清'
  if (!formData.seller_stamp) formData.seller_stamp = { show_stamp: false, stamp_url: '' }
  if (!formData.buyer_stamp) formData.buyer_stamp = { show_stamp: true, stamp_url: '/data/signatures/company_seal.png' }
  if (!Array.isArray(formData.clauses) || formData.clauses.length === 0) {
    formData.clauses = [
      '1. 本合同自签订之日起，盖章签字后生效。如需修改或终止时，应经双方协商同意，另立协议方可有效。',
      '2. 本合同在执行期间任何一方违约，由双方协商解决，违约需赔偿损失。',
      '3. 买方接收货物，视为卖方履行生产义务；检验不合格的部件由卖方补发，买方根据情况要求卖方承担相应的违约责任。',
      '4. 在未达成新的协议前，卖方如需调整价格，需提前一个月向买方协商，同时卖方不得影响买方的正常供货。',
    ]
  }
})

const clausesText = ref(Array.isArray(formData.clauses) ? formData.clauses.join('\n') : '')

watch(
  () => formData.clauses,
  (newClauses) => {
    if (Array.isArray(newClauses)) {
      clausesText.value = newClauses.join('\n')
    }
  },
  { deep: true }
)

function onClausesBlur() {
  formData.clauses = clausesText.value.split('\n').filter((s: string) => s.trim().length > 0)
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
}
.basic-title { color: #0284c7; }
.items-title { color: #059669; }
.terms-title { color: #0284c7; }
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

