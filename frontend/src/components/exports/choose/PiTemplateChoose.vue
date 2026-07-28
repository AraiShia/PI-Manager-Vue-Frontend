<template>
  <div class="template-card-grid">
    <div
      v-for="tpl in piTemplates"
      :key="tpl.id"
      class="template-card-item"
      :class="{ active: modelValue === tpl.id }"
      @click="selectTemplate(tpl.id)"
    >
      <!-- 选中提示 Check 徽标 -->
      <div v-if="modelValue === tpl.id" class="active-badge">
        <el-icon><Check /></el-icon>
      </div>

      <!-- 单据类型徽标 -->
      <div class="dept-badge-tag">
        <el-tag type="primary" size="small" effect="dark">
          PI 形式发票
        </el-tag>
      </div>

      <!-- A4 缩略图原型视觉效果 -->
      <div class="card-thumbnail-box">
        <div class="mini-doc-sheet">
          <div class="mini-header-bar">
            <div class="mini-company">{{ tpl.miniCompany }}</div>
            <div class="mini-title">{{ tpl.miniTitle }}</div>
          </div>
          <div class="mini-table-lines">
            <div class="mini-line th-line"></div>
            <div class="mini-line tr-line"></div>
            <div class="mini-line tr-line"></div>
            <div class="mini-line tr-line"></div>
          </div>
          <div class="mini-bottom">
            <div class="mini-bank-box"></div>
            <div class="mini-stamp-circle">印</div>
          </div>
        </div>
      </div>

      <!-- 卡片文字与标签 -->
      <div class="card-info-box">
        <div class="card-title-row">
          <span class="card-title">{{ tpl.title }}</span>
        </div>
        <div class="card-meta-row">
          <el-tag type="primary" size="small" plain>{{ tpl.subtitle }}</el-tag>
          <span class="version-text">Ver {{ tpl.version }}</span>
        </div>
        <div class="card-desc">{{ tpl.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview PI 形式发票专属模板选择组件 (PiTemplateChoose.vue)
 */
import { watch } from 'vue'
import { Check } from '@element-plus/icons-vue'

interface TemplateModel {
  id: string
  title: string
  subtitle: string
  version: string
  desc: string
  miniCompany: string
  miniTitle: string
}

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string]
}>()

const piTemplates: TemplateModel[] = [
  {
    id: 'pi_standard',
    title: '标准外贸 PI 模板',
    subtitle: '通用外贸',
    version: '2.1',
    desc: '标准的 10 列产品明细表排版，包含完整买卖双方、银行账号与电子公章。',
    miniCompany: 'WEINA TRADE CO., LTD.',
    miniTitle: 'PROFORMA INVOICE',
  },
  {
    id: 'pi_eu_compliant',
    title: '欧线合规 PI 模板',
    subtitle: '欧洲市场',
    version: '1.9',
    desc: '专为欧盟客户对齐 VAT 税号、EORI 号及符合欧盟海关查验规范的条款结构。',
    miniCompany: 'WEINA TRADE CO., LTD.',
    miniTitle: 'EU PROFORMA INVOICE',
  },
  {
    id: 'pi_express',
    title: '简易加急 PI 模板',
    subtitle: '样品/小单',
    version: '1.2',
    desc: '适合小批量样品订单快速开具，简化条款，突出交期与订金收款账号。',
    miniCompany: 'WEINA TRADE CO., LTD.',
    miniTitle: 'SAMPLE INVOICE',
  },
]

watch(
  () => piTemplates,
  (list) => {
    if (list.length > 0 && !props.modelValue) {
      emit('update:modelValue', list[0].id)
    }
  },
  { immediate: true }
)

function selectTemplate(id: string) {
  emit('update:modelValue', id)
}
</script>

<style scoped>
.template-card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.template-card-item {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background-color: #ffffff;
  padding: 12px;
  cursor: pointer;
  position: relative;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}
.template-card-item:hover {
  border-color: #409eff;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.15);
}
.template-card-item.active {
  border-color: #409eff;
  background-color: #f0f7ff;
  box-shadow: 0 4px 14px rgba(64, 158, 255, 0.2);
}
.active-badge {
  position: absolute;
  top: -1px;
  right: -1px;
  background-color: #409eff;
  color: #ffffff;
  width: 24px;
  height: 24px;
  border-bottom-left-radius: 8px;
  border-top-right-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  z-index: 5;
}
.dept-badge-tag {
  position: absolute;
  top: 6px;
  left: 6px;
  z-index: 4;
}
.card-thumbnail-box {
  width: 100%;
  height: 140px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ebedf0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 14px;
  margin-bottom: 12px;
  overflow: hidden;
  padding: 6px;
}
.mini-doc-sheet {
  width: 100%;
  height: 100%;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  padding: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.mini-company {
  font-size: 7px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}
.mini-title {
  font-size: 8px;
  font-weight: bold;
  color: #409eff;
  text-align: center;
  margin-top: 2px;
}
.mini-table-lines { margin: 4px 0; }
.mini-line {
  height: 4px;
  border-radius: 1px;
  margin-bottom: 3px;
}
.th-line { background-color: #409eff; }
.tr-line { background-color: #e4e7ed; }
.mini-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.mini-bank-box {
  width: 60%;
  height: 14px;
  background-color: #f2f6fc;
  border: 1px dashed #c0c4cc;
}
.mini-stamp-circle {
  width: 18px;
  height: 18px;
  border: 1px solid #f56c6c;
  color: #f56c6c;
  border-radius: 50%;
  font-size: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-info-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 13px;
  font-weight: bold;
  color: #303133;
  line-height: 1.3;
}
.card-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 2px 0;
}
.version-text {
  font-size: 11px;
  color: #c0c4cc;
  font-family: monospace;
}
.card-desc {
  font-size: 11px;
  color: #909399;
  line-height: 1.4;
  height: 32px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
