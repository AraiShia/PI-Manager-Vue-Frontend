<template>
  <div class="template-card-grid">
    <div
      v-for="tpl in purchaseTemplates"
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
        <el-tag type="danger" size="small" effect="dark">
          采购合同
        </el-tag>
      </div>

      <!-- A4 缩略图原型视觉效果 -->
      <div class="card-thumbnail-box">
        <div class="mini-doc-sheet">
          <div class="mini-header-bar">
            <div class="mini-company">{{ tpl.miniCompany }}</div>
            <div class="mini-title text-danger">{{ tpl.miniTitle }}</div>
          </div>
          <div class="mini-table-lines">
            <div class="mini-line th-line-danger"></div>
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
          <el-tag type="danger" size="small" plain>{{ tpl.subtitle }}</el-tag>
          <span class="version-text">Ver {{ tpl.version }}</span>
        </div>
        <div class="card-desc">{{ tpl.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview Purchase 采购合同专属模板选择组件 (PurchaseTemplateChoose.vue)
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

const purchaseTemplates: TemplateModel[] = [
  {
    id: 'po_standard',
    title: '标准工厂采购合同',
    subtitle: '国内采购',
    version: '3.0',
    desc: '国内工厂采购合同模板，严格约定产品规格、工厂交货工期及质检标准。',
    miniCompany: 'WEINA PURCHASING DEPT.',
    miniTitle: 'PURCHASE CONTRACT',
  },
  {
    id: 'po_framework',
    title: '框架合作采购协议',
    subtitle: '长期供应商',
    version: '2.0',
    desc: '针对长期战略合作工厂，按批次发货核算、分期付款与尾款账期协议。',
    miniCompany: 'WEINA PURCHASING DEPT.',
    miniTitle: 'PURCHASE AGREEMENT',
  },
]

watch(
  () => purchaseTemplates,
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
  border-color: #f56c6c;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.15);
}
.template-card-item.active {
  border-color: #f56c6c;
  background-color: #fef0f0;
  box-shadow: 0 4px 14px rgba(245, 108, 108, 0.2);
}
.active-badge {
  position: absolute;
  top: -1px;
  right: -1px;
  background-color: #f56c6c;
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
  text-align: center;
  margin-top: 2px;
}
.text-danger { color: #f56c6c; }
.mini-table-lines { margin: 4px 0; }
.mini-line {
  height: 4px;
  border-radius: 1px;
  margin-bottom: 3px;
}
.th-line-danger { background-color: #f56c6c; }
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
