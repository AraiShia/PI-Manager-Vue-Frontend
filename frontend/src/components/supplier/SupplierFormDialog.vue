<template>
  <el-dialog
    :model-value="modelValue"
    :title="supplier ? '编辑供应商' : '新建供应商'"
    width="780px"
    destroy-on-close
    :close-on-click-modal="false"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="供应商编号" prop="supplier_code">
            <el-input v-model="form.supplier_code" :disabled="!!supplier" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="供应商名称" prop="supplier_name">
            <el-input v-model="form.supplier_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="省份">
            <el-select v-model="form.province" filterable clearable class="full-width" @change="onProvinceChange">
              <el-option v-for="item in provinces" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="城市">
            <el-select v-model="form.city" filterable clearable class="full-width">
              <el-option v-for="item in cities" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系人">
            <el-input v-model="form.contact_person" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="电话">
            <el-input v-model="form.phone" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="邮箱">
            <el-input v-model="form.email" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="地址">
            <el-input v-model="form.address" type="textarea" :rows="2" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { suppliersApi, type Supplier } from '@/api/suppliers'

const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [supplier: Supplier]
}>()

const formRef = ref<FormInstance>()
const saving = ref(false)
const provinces = ref<string[]>([])
const cities = ref<string[]>([])

const emptyForm = () => ({
  supplier_code: '',
  supplier_name: '',
  province: '',
  city: '',
  contact_person: '',
  phone: '',
  email: '',
  address: '',
})

const form = reactive(emptyForm())

const rules: FormRules = {
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
}

// 监听 supplier prop 变化，填充或重置表单
watch(() => props.supplier, (s) => {
  if (s) {
    Object.assign(form, emptyForm(), {
      supplier_code: s.supplier_code || '',
      supplier_name: s.supplier_name || '',
      province: s.province || '',
      city: s.city || '',
      contact_person: s.contact_person || '',
      phone: s.phone || '',
      email: s.email || '',
      address: s.address || '',
    })
    if (s.province) {
      loadCities(s.province, s.city)
    }
  } else {
    Object.assign(form, emptyForm())
  }
  cities.value = []
}, { immediate: true })

// 监听弹窗打开时加载省份列表
watch(() => props.modelValue, async (visible) => {
  if (visible && provinces.value.length === 0) {
    try {
      const res = await suppliersApi.provinces()
      provinces.value = res.data || []
    } catch (e) {
      console.warn('[SupplierFormDialog] 加载省份失败', e)
    }
  }
})

async function onProvinceChange(value?: string) {
  cities.value = []
  if (!value) return
  await loadCities(value)
}

async function loadCities(province: string, initialCity?: string) {
  try {
    const res = await suppliersApi.cities(province)
    cities.value = res.data || []
    if (initialCity && !cities.value.includes(initialCity)) {
      form.city = ''
    }
  } catch (e) {
    console.warn('[SupplierFormDialog] 加载城市失败', e)
  }
}

async function save() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (props.supplier) {
      await suppliersApi.update(props.supplier.id, {
        supplier_name: form.supplier_name,
        province: form.province || null,
        city: form.city || null,
        contact_person: form.contact_person || null,
        phone: form.phone || null,
        email: form.email || null,
        address: form.address || null,
      })
      ElMessage.success('供应商已更新')
    } else {
      const res = await suppliersApi.create({
        supplier_code: form.supplier_code,
        supplier_name: form.supplier_name,
        province: form.province || null,
        city: form.city || null,
        contact_person: form.contact_person || null,
        phone: form.phone || null,
        email: form.email || null,
        address: form.address || null,
      })
      ElMessage.success('供应商已创建')
      emit('success', res.data)
    }
    emit('update:modelValue', false)
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
