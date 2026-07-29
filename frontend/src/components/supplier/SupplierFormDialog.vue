<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="560px"
    :close-on-click-modal="false"
    :before-close="requestClose"
  >
    <!-- 平台 Tabs：新建或历史数据（platform=NULL）时可切换 -->
    <el-tabs v-if="!hasPlatform" v-model="currentPlatform" class="platform-tabs">
      <el-tab-pane label="线上采购" name="online" />
      <el-tab-pane label="线下采购" name="offline" />
    </el-tabs>

    <!-- 已有 platform 的供应商，Tabs 锁定为该值 -->
    <div v-else class="platform-locked">
      <el-tag type="info">{{ platformLabelMap[currentPlatform] }}</el-tag>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="supplier-form">
      <!-- 供应商名称 -->
      <el-form-item label="供应商名称" prop="supplier_name">
        <el-input v-model="form.supplier_name" placeholder="请输入供应商名称" />
      </el-form-item>
      <el-form-item label="采购方式" prop="supply_mode">
        <el-input v-model="form.supply_mode" placeholder="采购方式" />
      </el-form-item>
      <el-form-item label="微信" prop="supplier_wechat">
        <el-input v-model="form.supplier_wechat" placeholder="微信号" />
      </el-form-item>

      <!-- 通用字段 -->
      <el-form-item label="联系人">
        <el-input v-model="form.contact_person" placeholder="选填" />
      </el-form-item>
      <el-form-item label="电话">
        <el-input v-model="form.phone" placeholder="选填" />
      </el-form-item>
      <el-form-item label="省份">
        <el-select v-model="form.province" placeholder="请选择省份" clearable filterable allow-create>
          <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item label="城市" v-if="form.province">
        <el-select v-model="form.city" placeholder="请选择城市" clearable filterable allow-create>
          <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="requestClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { suppliersApi } from '@/api/suppliers'
import type { Supplier } from '@/api/suppliers'

const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
  defaultPlatform?: 'online' | 'offline'
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  'success': [supplier: Supplier]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const dialogTitle = computed(() => props.supplier ? '编辑供应商' : '新建供应商')
const hasPlatform = computed(() => !!props.supplier?.platform)
const currentPlatform = ref<'online' | 'offline'>(
  (props.supplier?.platform as any) || props.defaultPlatform || 'offline'
)

const platformLabelMap: Record<string, string> = {
  'online': '线上采购',
  'offline': '线下采购',
}

const formRef = ref<FormInstance>()
const saving = ref(false)

const form = ref({
  supplier_name: '',
  supply_mode: '',
  supplier_wechat: '',
  wechat_id: '',
  wechat_nickname: '',
  is_dropship: false,
  contact_person: '',
  phone: '',
  province: '',
  city: '',
})

// 加载已有供应商数据到表单
watch(() => props.supplier, (s) => {
  if (s) {
    form.value = {
      supplier_name: s.supplier_name || '',
      supply_mode: s.supply_mode || '',
      supplier_wechat: s.supplier_wechat || '',
      wechat_id: s.wechat_id || '',
      wechat_nickname: s.wechat_nickname || '',
      is_dropship: s.is_dropship || false,
      contact_person: s.contact_person || '',
      phone: s.phone || '',
      province: s.province || '',
      city: s.city || '',
    }
  } else {
    form.value = { supplier_name: '', supply_mode: '', supplier_wechat: '', wechat_id: '', wechat_nickname: '', is_dropship: false, contact_person: '', phone: '', province: '', city: '' }
    currentPlatform.value = props.defaultPlatform || 'offline'
  }
}, { immediate: true })

const rules: FormRules = {
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
}

const provinces = ref<string[]>([])
const cities = ref<string[]>([])

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

watch(() => form.value.province, (p) => {
  if (p) {
    suppliersApi.cities(p).then((res) => {
      cities.value = res.data || []
    }).catch(() => {
      cities.value = []
    })
  } else {
    cities.value = []
    form.value.city = ''
  }
})

async function save() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload: any = {
      supplier_name: form.value.supplier_name,
      supply_mode: form.value.supply_mode || null,
      supplier_wechat: form.value.supplier_wechat || null,
      province: form.value.province || null,
      city: form.value.city || null,
      contact_person: form.value.contact_person || null,
      phone: form.value.phone || null,
      platform: currentPlatform.value,
    }
    const res = props.supplier
      ? await suppliersApi.update(props.supplier.id, payload)
      : await suppliersApi.create(payload)
    const supplierData = res?.data || res
    if (supplierData) {
      ElMessage.success(props.supplier ? '供应商已更新' : '供应商已创建')
      emit('success', supplierData)
      visible.value = false
    } else {
      ElMessage.error('创建供应商未返回有效数据')
    }
  } catch (e: any) {
    const message =
      e?.response?.data?.detail ||
      e?.response?.data?.message ||
      e?.message ||
      '保存失败'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

function requestClose() {
  visible.value = false
}
</script>

<style scoped>
.platform-tabs { margin-bottom: 16px; }
.platform-locked { margin-bottom: 16px; }
.supplier-form { margin-top: 8px; }
</style>
