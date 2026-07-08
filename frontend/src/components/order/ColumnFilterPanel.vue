<template>
  <div class="col-filter-panel" data-testid="col-filter-panel">
    <div class="col-filter-title">显示 / 隐藏列</div>
    <div class="col-filter-grid">
      <el-checkbox
        v-for="col in options"
        :key="col.key"
        :model-value="state[col.key]"
        :label="col.locked ? `${col.label}（锁定）` : col.label"
        :disabled="col.locked"
        @change="(val) => onToggle(col, val)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElCheckbox } from 'element-plus'
import type { ColumnOption, ColumnVisibilityState } from '@/utils/columnVisibility'

const props = defineProps<{
  options: ColumnOption[]
  state: ColumnVisibilityState
}>()

const emit = defineEmits<{
  (e: 'toggle', key: string, value: boolean): void
}>()

function onToggle(col: ColumnOption, value: boolean | string | number) {
  if (col.locked) return
  const bool = typeof value === 'boolean' ? value : Boolean(value)
  emit('toggle', col.key, bool)
}
</script>
