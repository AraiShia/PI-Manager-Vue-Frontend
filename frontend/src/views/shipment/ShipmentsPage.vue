<template>
  <div class="shipments-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">出货管理</h2>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="onCreateShipment">
          新建出货单
        </el-button>
      </div>
    </div>

    <ShipmentListPanel />

    <ShipmentCreateDialog ref="createDialogRef" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import ShipmentListPanel from '@/components/shipment/ShipmentListPanel.vue'
import ShipmentCreateDialog from '@/components/shipment/ShipmentCreateDialog.vue'

const createDialogRef = ref<InstanceType<typeof ShipmentCreateDialog> | null>(null)

function onCreateShipment() {
  createDialogRef.value?.open()
}
</script>

<style scoped>
.shipments-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
</style>
