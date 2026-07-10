<template>
  <el-dialog
    v-model="visible"
    title="创建出货单"
    width="900px"
    :close-on-click-modal="false"
    @close="onDialogClose"
  >
    <ShipmentProductPicker
      ref="productPickerRef"
      :pre-selected-pi-ids="preSelectedPiIds"
      @update:selected-items="onItemsChange"
    />

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="saving"
        :disabled="selectedItems.length === 0"
        @click="onSubmit"
      >
        创建出货单 ({{ selectedItems.length }} 项)
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useShipmentStore } from '@/stores/shipmentStore'
import ShipmentProductPicker from './ShipmentProductPicker.vue'
import type { ShipmentCreateItem } from '@/types/shipment'

const props = defineProps<{
  preSelectedPiIds?: number[]
}>()

const store = useShipmentStore()
const visible = ref(false)
const saving = ref(false)
const selectedItems = ref<ShipmentCreateItem[]>([])
const productPickerRef = ref<InstanceType<typeof ShipmentProductPicker> | null>(null)

function open() {
  visible.value = true
}

function onDialogClose() {
  selectedItems.value = []
}

function onItemsChange(items: ShipmentCreateItem[]) {
  selectedItems.value = items
}

async function onSubmit() {
  if (selectedItems.value.length === 0) return
  saving.value = true
  try {
    // 从选中行原始数据中提取 pi_id（需要从 productPickerRef 获取原始行）
    const rows = productPickerRef.value?.selectedRows ?? []
    const piIdSet = new Set<number>()
    rows.forEach((r: any) => {
      if (r._shipQty > 0) piIdSet.add(r.pi_id)
    })
    const piIds = Array.from(piIdSet)
    if (piIds.length === 0) {
      ElMessage.warning('请至少选择一个 PI')
      return
    }
    const result = await store.createFromOrders({
      dept_id: 'S',
      pi_ids: piIds,
      items: selectedItems.value,
    })
    if (result) {
      visible.value = false
    }
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
