<template>
  <SupplierFormDialog
    v-model="visible"
    :supplier="null"
    @success="onSuccess"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Supplier } from '@/api/suppliers'
import SupplierFormDialog from '@/components/supplier/SupplierFormDialog.vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [supplier: Supplier]
}>()

const visible = ref(props.modelValue)

watch(() => props.modelValue, v => { visible.value = v })
watch(visible, v => { emit('update:modelValue', v) })

function onSuccess(supplier: Supplier) {
  visible.value = false
  emit('success', supplier)
}
</script>
