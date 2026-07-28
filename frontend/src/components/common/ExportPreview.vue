<template>
  <div class="export-preview-wrapper">
    <!-- 1. 统一顶栏控制条：选择单据类型、编辑弹窗触发、打印与导出操作 -->
    <div class="export-toolbar no-print">
      <div class="toolbar-left">
        <el-radio-group v-model="activeTab" size="large" @change="onTabChange">
          <el-radio-button label="pi">PROFORMA INVOICE (PI 形式发票)</el-radio-button>
          <el-radio-button label="ci">COMMERCIAL INVOICE (CI 商业发票)</el-radio-button>
          <el-radio-button label="pl">PACKING LIST (PL 装箱单)</el-radio-button>
          <el-radio-button label="purchase">PURCHASE INVOICE (采购合同)</el-radio-button>
        </el-radio-group>
      </div>

      <div class="toolbar-right">
        <el-button type="info" :icon="Document" plain @click="openChooseModal">
          选择单据模板
        </el-button>
        <el-button type="warning" :icon="Edit" plain @click="openEditModal">
          编辑单据内容
        </el-button>
        <el-button type="primary" :icon="Printer" plain @click="handlePrint">
          打印 / 另存为 PDF
        </el-button>
        <el-button type="success" :icon="Download" @click="handleExportExcel">
          导出 Excel (.xlsx)
        </el-button>
      </div>
    </div>

    <!-- 2. 单据视图核心展示容器 (只读高保真渲染模式) -->
    <div class="doc-content-container">
      <!-- PI (形式发票) 模块 -->
      <div v-show="activeTab === 'pi'">
        <PIExportExample ref="piExportRef" :is-edit-mode="false" />
      </div>

      <!-- CI (商业发票) 模块 -->
      <div v-show="activeTab === 'ci'">
        <CIExportExample ref="ciExportRef" :is-edit-mode="false" />
      </div>

      <!-- PL (装箱单) 模块 -->
      <div v-show="activeTab === 'pl'">
        <PLExportExample ref="plExportRef" :is-edit-mode="false" />
      </div>

      <!-- Purchase Invoice (采购合同) 模块 -->
      <div v-show="activeTab === 'purchase'">
        <PurchaseInvoiceExportExample ref="purchaseExportRef" :is-edit-mode="false" />
      </div>
    </div>

    <!-- 3. 视觉模板卡片选择器弹窗 -->
    <ExportExampleChoose
      v-model="chooseModalVisible"
      :default-type="activeTab"
      @confirm="onTemplateChosen"
    />

    <!-- 4. 通用编辑弹窗：嵌套对应的单据原型组件进行大表单与签章配置 -->
    <ExportEditModal
      v-model="editModalVisible"
      :doc-type="activeTab"
      @save="onExportEditSaved"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @fileoverview 统一全单据导出与打印预览大中心组件 (ExportPreview.vue)
 * 职责描述：
 * 1. 集中管理 PI (形式发票)、CI (商业发票)、PL (装箱单)、Purchase Invoice (采购合同) 的视图预览
 * 2. 主页面展示区呈现纯净高保真的单据 Sheet (无任何编辑框)
 * 3. 顶部“编辑单据内容”按钮弹出 ExportEditModal，以对话框形式进行可视化全表单编辑
 * 4. 支持通过路由 Query 参数 `type=pi|ci|pl|purchase` 及 `edit=true` 默认触发
 */

import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Printer, Download, Edit, Document } from '@element-plus/icons-vue'
import { useOrderSummaryStore } from '@/stores/orderSummaryStore'
// 导入各种单据模板的导出/预览示例组件（各自位于对应的子目录中）
import PIExportExample from '@/components/exports/PI/PIExportExample.vue'
import CIExportExample from '@/components/exports/CI/CIExportExample.vue'
import PLExportExample from '@/components/exports/PL/PLExportExample.vue'
import PurchaseInvoiceExportExample from '@/components/exports/PO/PurchaseInvoiceExportExample.vue'
import ExportEditModal from '@/components/exports/ExportEditModal.vue'
import ExportExampleChoose from '@/components/exports/ExportExampleChoose.vue'

const route = useRoute()
const router = useRouter()
const store = useOrderSummaryStore()

/** 当前选中的单据类型: 'pi' | 'ci' | 'pl' | 'purchase' */
const activeTab = ref<'pi' | 'ci' | 'pl' | 'purchase'>('pi')

/** 是否弹出模板选择框 */
const chooseModalVisible = ref<boolean>(false)

/** 是否弹出编辑对话框 */
const editModalVisible = ref<boolean>(false)

/** 子组件引用实例 */
const piExportRef = ref<InstanceType<typeof PIExportExample> | null>(null)
const ciExportRef = ref<InstanceType<typeof CIExportExample> | null>(null)
const plExportRef = ref<InstanceType<typeof PLExportExample> | null>(null)
const purchaseExportRef = ref<InstanceType<typeof PurchaseInvoiceExportExample> | null>(null)

/** 打开模板选择框 */
function openChooseModal() {
  chooseModalVisible.value = true
}

/** 选择模板后直接打开编辑弹窗 */
function onTemplateChosen(templateId: string, docType: 'pi' | 'ci' | 'pl' | 'purchase') {
  activeTab.value = docType
  router.replace({
    query: { ...route.query, type: docType, template: templateId },
  })
  // 选定模板后直接打开大表单编辑弹窗！
  editModalVisible.value = true
}

/** 打开编辑弹窗 */
function openEditModal() {
  editModalVisible.value = true
}

/** 编辑弹窗保存回调，同步更新 Pinia 中的 exportDocData */
function onExportEditSaved(data: any) {
  store.setExportDocData(data)
  editModalVisible.value = false
}

/** 切换 Tab 时同步更新 URL Query 属性 */
function onTabChange(tabVal: string | number | boolean) {
  router.replace({
    query: { ...route.query, type: String(tabVal) },
  })
}

/** 执行通用打印/另存为 PDF */
function handlePrint() {
  window.print()
}

/** 执行当前激活单据的 Excel 导出 */
function handleExportExcel() {
  if (activeTab.value === 'pi') {
    piExportRef.value?.handleExportExcel()
  } else if (activeTab.value === 'ci') {
    ciExportRef.value?.handleExportExcel()
  } else if (activeTab.value === 'pl') {
    plExportRef.value?.handleExportExcel()
  } else if (activeTab.value === 'purchase') {
    purchaseExportRef.value?.handleExportExcel()
  }
}

onMounted(async () => {
  // 校验并恢复缓存中的导出数据
  store.loadExportDocData()

  // 如果 Query 含有 order_id，尝试拉取对应订单详情（若 store 无当前订单）
  if (route.query.order_id) {
    const orderIdNum = Number(route.query.order_id)
    if (orderIdNum && (!store.currentOrder || store.currentOrder.id !== orderIdNum)) {
      await store.fetchOrderDetail(orderIdNum)
    }
  }

  if (route.query.type && typeof route.query.type === 'string') {
    const validTypes = ['pi', 'ci', 'pl', 'purchase'] as const
    if (validTypes.includes(route.query.type as any)) {
      activeTab.value = route.query.type as 'pi' | 'ci' | 'pl' | 'purchase'
    }
  }

  // 若携带 choose=true 参数，自动拉起该单据类型的模板选择框！
  if (route.query.choose === 'true') {
    openChooseModal()
  } else if (route.query.edit === 'true') {
    // 若携带 edit=true 参数，自动拉起编辑弹窗
    openEditModal()
  }
})
</script>

<style scoped>
/* 导出与打印预览大中心根容器：启用 100vh 独立垂直滚动 */
.export-preview-wrapper {
  height: 100vh;
  overflow-y: auto;
  box-sizing: border-box;
  background-color: #f5f7fa;
  font-family: 'Times New Roman', Times, SimSun, Georgia, serif;
}

/* 统一顶栏控制条 */
.export-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mode-tag {
  font-size: 13px;
}

.doc-content-container {
  padding-bottom: 40px;
}

/* 打印专用的 CSS 媒体查询：导出或打印时隐藏按钮及工具栏，重置高度与滚动条 */
@media print {
  .no-print {
    display: none !important;
  }
  .export-preview-wrapper {
    background: none !important;
    height: auto !important;
    overflow: visible !important;
  }
}
</style>
