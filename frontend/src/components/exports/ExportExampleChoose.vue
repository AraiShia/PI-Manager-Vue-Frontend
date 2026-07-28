<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="920px"
    top="8vh"
    destroy-on-close
    class="export-choose-dialog"
    :close-on-click-modal="false"
  >
    <div class="choose-dialog-body">
      <div class="choose-subheading">
        请选择你需要调用的单据样式模板。选定模板后，系统将自动注入订单真实数据并进入编辑确认界面：
      </div>

      <!-- 动态选择器卡片容器 -->
      <component :is="activeChooseComponent" v-model="selectedTemplateId" />
    </div>

    <template #footer>
      <div class="choose-dialog-footer">
        <el-button @click="onCancel">取消</el-button>
        <el-button type="primary" size="large" @click="onConfirmNext">
          下一步：编辑单据数据 ➔
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @fileoverview 入口驱动单据模板选择器 (ExportExampleChoose.vue)
 * 采用多子组件动态挂载架构 (Multi-subform Choose Architecture)，
 * 根据传入的 docType 自动匹配渲染 PiTemplateChoose / CiTemplateChoose / PlTemplateChoose / PurchaseTemplateChoose。
 */

import { ref, computed, watch } from 'vue'

import PiTemplateChoose from './choose/PiTemplateChoose.vue'
import CiTemplateChoose from './choose/CiTemplateChoose.vue'
import PlTemplateChoose from './choose/PlTemplateChoose.vue'
import PurchaseTemplateChoose from './choose/PurchaseTemplateChoose.vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    docType?: 'pi' | 'ci' | 'pl' | 'purchase'
  }>(),
  {
    modelValue: false,
    docType: 'pi',
  }
)

const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  confirm: [templateId: string, docType: 'pi' | 'ci' | 'pl' | 'purchase']
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

/** 动态匹配激活对应的单据模板选择器子组件 */
const activeChooseComponent = computed(() => {
  switch (props.docType) {
    case 'ci':
      return CiTemplateChoose
    case 'pl':
      return PlTemplateChoose
    case 'purchase':
      return PurchaseTemplateChoose
    case 'pi':
    default:
      return PiTemplateChoose
  }
})

const dialogTitle = computed(() => {
  switch (props.docType) {
    case 'pi':
      return '请选择 PROFORMA INVOICE (PI 形式发票) 模板'
    case 'ci':
      return '请选择 COMMERCIAL INVOICE (CI 商业发票) 模板'
    case 'pl':
      return '请选择 PACKING LIST (PL 装箱单) 模板'
    case 'purchase':
      return '请选择 PURCHASE INVOICE (采购合同) 模板'
    default:
      return '请选择单据模板'
  }
})

/** 当前选中的模板 ID */
const selectedTemplateId = ref<string>('pi_standard')

watch(
  () => props.docType,
  (newType) => {
    switch (newType) {
      case 'ci':
        selectedTemplateId.value = 'ci_standard'
        break
      case 'pl':
        selectedTemplateId.value = 'pl_standard'
        break
      case 'purchase':
        selectedTemplateId.value = 'po_standard'
        break
      case 'pi':
      default:
        selectedTemplateId.value = 'pi_standard'
        break
    }
  },
  { immediate: true }
)

function onCancel() {
  visible.value = false
}

function onConfirmNext() {
  emit('confirm', selectedTemplateId.value, props.docType)
  visible.value = false
}
</script>

<style scoped>
/* 模板选择弹窗体样式：控制最大高度并启用滚动条 */
.export-choose-dialog :deep(.el-dialog__body) {
  padding: 16px 24px;
  max-height: 75vh;
  overflow-y: auto;
}
.choose-subheading {
  font-size: 13px;
  color: #606266;
  margin-bottom: 20px;
}
.choose-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>