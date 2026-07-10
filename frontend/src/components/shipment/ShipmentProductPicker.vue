<template>
  <div class="shipment-product-picker">
    <!-- PI 选择区 -->
    <div class="picker-section">
      <div class="section-label">选择 PI</div>
      <el-select
        v-model="selectedPiIds"
        multiple
        filterable
        placeholder="请选择 PI（支持多选）"
        style="width: 100%"
        @change="onPiSelectionChange"
      >
        <el-option
          v-for="pi in availablePis"
          :key="pi.id"
          :label="`${pi.pi_no} - ${pi.customer_name || ''}`"
          :value="pi.id"
        />
      </el-select>
    </div>

    <!-- 可出货明细表格 -->
    <div v-if="selectedPiIds.length > 0" class="picker-section picker-table">
      <div class="section-label">
        选择产品（已选 {{ selectedCount }} 项，合计 {{ totalQuantity }} 件）
      </div>
      <el-table
        v-loading="loading"
        :data="shippableItems"
        stripe
        border
        max-height="400"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="45" align="center" />

        <el-table-column prop="pi_no" label="PI号" width="140" show-overflow-tooltip />

        <el-table-column prop="customer_code" label="客户编号" width="100" show-overflow-tooltip />

        <el-table-column prop="oe_number" label="OE号" width="120" show-overflow-tooltip />

        <el-table-column prop="product_name" label="产品名称" min-width="160" show-overflow-tooltip />

        <el-table-column prop="order_quantity" label="订单数量" width="90" align="right">
          <template #default="{ row }">{{ row.order_quantity.toFixed(0) }}</template>
        </el-table-column>

        <el-table-column prop="shipped_quantity" label="已出货" width="90" align="right">
          <template #default="{ row }">{{ row.shipped_quantity.toFixed(0) }}</template>
        </el-table-column>

        <el-table-column prop="remaining_quantity" label="可出货" width="90" align="right">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600">{{ row.remaining_quantity.toFixed(0) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="本次出货数量" width="140" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row._shipQty"
              :min="0"
              :max="row.remaining_quantity"
              :step="1"
              size="small"
              style="width: 110px"
              :disabled="!selectedRows.includes(row)"
            />
          </template>
        </el-table-column>

        <el-table-column label="出货单价" width="110" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row._unitPrice"
              :min="0"
              :precision="2"
              :step="0.01"
              size="small"
              style="width: 90px"
              :disabled="!selectedRows.includes(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="请先选择 PI" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { shipmentsApi } from '@/api/shipments'
import { orderSummaryApi } from '@/api/orderSummary'
import type { ShippableItem, ShipmentCreateItem } from '@/types/shipment/index'
import type { OrderListItem } from '@/types/orderSummary'
import { isFormalOrderStatus } from '@/utils/formalRecord'

interface PiOption {
  id: number
  pi_no: string
  customer_name: string
}

const props = defineProps<{
  /** 预选的 PI IDs（如从当前订单传入） */
  preSelectedPiIds?: number[]
}>()

const emit = defineEmits<{
  (e: 'update:selectedItems', items: ShipmentCreateItem[]): void
}>()

const availablePis = ref<PiOption[]>([])
const selectedPiIds = ref<number[]>([])
const shippableItems = ref<(ShippableItem & { _shipQty: number; _unitPrice: number })[]>([])
const selectedRows = ref<any[]>([])
const loading = ref(false)
const piLoading = ref(false)

// 加载已保存正式纪录的 PI 列表
async function loadAvailablePis() {
  piLoading.value = true
  try {
    const res = await orderSummaryApi.getOrders({ page: 1, page_size: 100 })
    const orders = res.data.code === 200
      ? res.data.data.list.filter(pi => isFormalOrderStatus(pi.status))
      : []
    availablePis.value = orders.map((pi: OrderListItem) => ({
      id: pi.id,
      pi_no: pi.pi_no,
      customer_name: pi.customer_name || '',
    }))
    // 如果有预选 PI，初始化选中
    if (props.preSelectedPiIds?.length) {
      selectedPiIds.value = props.preSelectedPiIds.filter(id =>
        availablePis.value.some(p => p.id === id)
      )
      if (selectedPiIds.value.length > 0) {
        onPiSelectionChange()
      }
    }
  } catch (e) {
    console.error('加载正式 PI 列表失败', e)
  } finally {
    piLoading.value = false
  }
}

async function onPiSelectionChange() {
  if (selectedPiIds.value.length === 0) {
    shippableItems.value = []
    selectedRows.value = []
    emit('update:selectedItems', [])
    return
  }
  loading.value = true
  try {
    const res = await shipmentsApi.getShippableItems(selectedPiIds.value)
    if (res.data.code === 200) {
      shippableItems.value = (res.data.data as ShippableItem[]).map(item => ({
        ...item,
        _shipQty: 0,
        _unitPrice: item.unit_price,
      }))
    }
  } catch (e) {
    console.error('加载可出货产品失败', e)
  } finally {
    loading.value = false
  }
}

function onSelectionChange(selection: any[]) {
  selectedRows.value = selection
  // 同步 _shipQty 到 0（如果从选中变为未选中）
  const selectedIds = new Set(selection.map(r => r.pi_item_id))
  shippableItems.value.forEach(item => {
    if (!selectedIds.has(item.pi_item_id)) {
      item._shipQty = 0
    }
  })
  emitSelection()
}

const selectedCount = computed(() => selectedRows.value.length)

const totalQuantity = computed(() =>
  selectedRows.value.reduce((sum, row) => sum + (row._shipQty || 0), 0)
)

function emitSelection() {
  const items: ShipmentCreateItem[] = selectedRows.value
    .filter(row => row._shipQty > 0)
    .map(row => ({
      pi_item_id: row.pi_item_id,
      product_id: row.product_id,
      shipment_quantity: row._shipQty,
      unit_price: row._unitPrice,
    }))
  emit('update:selectedItems', items)
}

// 监听数量变化
watch(
  () => shippableItems.value.map(r => ({ qty: r._shipQty, price: r._unitPrice })),
  emitSelection,
  { deep: true }
)

// 暴露加载方法和原始选中行
defineExpose({ loadAvailablePis, selectedRows })

// 初始化
loadAvailablePis()
</script>

<style scoped>
.shipment-product-picker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.picker-section {
  background: #fff;
}
.picker-table {
  margin-top: 0;
}
.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}
</style>
