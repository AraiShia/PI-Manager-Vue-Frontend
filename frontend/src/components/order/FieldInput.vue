<template>
  <div class="field-input-wrapper">
    <el-input
      :model-value="displayValue"
      :class="['field-input', statusClass]"
      :disabled="props.disabled"
      @update:model-value="onInput"
      @blur="onBlur"
    >
      <template v-if="$slots.suffix" #suffix>
        <slot name="suffix" />
      </template>
    </el-input>
    <div class="field-status-slot">
      <el-icon v-if="status === 'saving'" class="field-status-icon is-loading"><Loading /></el-icon>
      <el-icon v-else-if="status === 'success'" class="field-status-icon success"><Check /></el-icon>
      <el-icon v-else-if="status === 'error'" class="field-status-icon error"><CircleClose /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading, Check, CircleClose } from '@element-plus/icons-vue'
import type { FieldStatus } from '@/composables/useProductEdit'

const props = defineProps<{
  modelValue: string | number | null | undefined
  status?: FieldStatus
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'blur'): void
}>()

const displayValue = computed(() => {
  const v = props.modelValue
  if (v === null || v === undefined) return ''
  return String(v)
})

const statusClass = computed(() => props.status || 'idle')

function onInput(value: string) {
  emit('update:modelValue', value)
}

function onBlur() {
  emit('blur')
}
</script>

<style scoped>
.field-input-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field-input-wrapper .field-input {
  flex: 1;
  min-width: 0;
}

.field-status-slot {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.field-status-icon {
  font-size: 16px;
}

.field-status-icon.is-loading {
  color: #409eff;
}

.field-status-icon.success {
  color: #67c23a;
}

.field-status-icon.error {
  color: #f56c6c;
}

:deep(.field-input.success .el-input__inner) {
  border-color: #67c23a;
}

:deep(.field-input.error .el-input__inner) {
  border-color: #f56c6c;
}
</style>
