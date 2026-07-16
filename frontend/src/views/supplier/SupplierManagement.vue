<template>
  <main class="supplier-page">
    <section class="supplier-toolbar">
      <div class="title-area">
        <h1>供应商管理</h1>
        <span>{{ filteredSuppliers.length }} 条记录</span>
      </div>
      <div class="filters">
        <el-input v-model="filters.search" clearable class="search-input" placeholder="搜索编号/名称/联系人/电话" @keyup.enter="applyFilters" />
        <el-select v-model="filters.province" clearable placeholder="全部省份" class="filter-select">
          <el-option v-for="item in provinces" :key="item" :label="item" :value="item" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="applyFilters">搜索</el-button>
        <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增供应商</el-button>
        <el-button :icon="Refresh" @click="loadSuppliers">刷新</el-button>
      </div>
    </section>

    <section class="table-wrap">
      <el-table
        v-loading="loading"
        :data="filteredSuppliers"
        border
        height="calc(100vh - 210px)"
        row-key="id"
        empty-text="暂无供应商数据"
      >
        <el-table-column prop="supplier_code" label="供应商编号" width="130" show-overflow-tooltip />
        <el-table-column prop="supplier_name" label="供应商名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="省份" width="100" prop="province" show-overflow-tooltip />
        <el-table-column label="城市" width="100" prop="city" show-overflow-tooltip />
        <el-table-column label="联系人" width="100" prop="contact_person" show-overflow-tooltip />
        <el-table-column label="电话" width="130" prop="phone" show-overflow-tooltip />
        <el-table-column label="邮箱" width="180" prop="email" show-overflow-tooltip />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link :type="row.status === 1 ? 'danger' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="removeSupplier(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingSupplier ? '编辑供应商' : '新增供应商'"
      width="780px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="supplier-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="供应商编号" prop="supplier_code">
              <el-input v-model="form.supplier_code" :disabled="!!editingSupplier" />
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSupplier">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { suppliersApi, type Supplier } from '@/api/suppliers'

const loading = ref(false)
const saving = ref(false)
const suppliers = ref<Supplier[]>([])
const provinces = ref<string[]>([])
const cities = ref<string[]>([])
const dialogVisible = ref(false)
const editingSupplier = ref<Supplier | null>(null)
const formRef = ref<FormInstance>()

const filters = reactive({
  search: '',
  province: undefined as string | undefined,
})

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
  supplier_code: [{ required: true, message: '请输入供应商编号', trigger: 'blur' }],
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
}

const filteredSuppliers = computed(() => {
  const keyword = filters.search.trim().toLowerCase()
  return suppliers.value.filter(item => {
    if (filters.province && item.province !== filters.province) return false
    if (!keyword) return true
    return [item.supplier_code, item.supplier_name, item.contact_person, item.phone].some(
      value => typeof value === 'string' && value.toLowerCase().includes(keyword)
    )
  })
})

async function loadSuppliers() {
  loading.value = true
  try {
    const res = await suppliersApi.list({ limit: 1000 })
    suppliers.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function loadProvinces() {
  try {
    const res = await suppliersApi.provinces()
    provinces.value = res.data || []
  } catch (err) {
    console.warn('[供应商] 加载省份失败', err)
  }
}

async function onProvinceChange(value?: string, preserveCity = false) {
  cities.value = []
  if (!preserveCity) {
    form.city = ''
  }
  if (!value) return
  try {
    const res = await suppliersApi.cities(value)
    cities.value = res.data || []
  } catch (err) {
    console.warn('[供应商] 加载城市失败', err)
  }
}

function applyFilters() { /* computed */ }

function resetFilters() {
  filters.search = ''
  filters.province = undefined
}

function openCreate() {
  editingSupplier.value = null
  Object.assign(form, emptyForm())
  cities.value = []
  dialogVisible.value = true
}

function openEdit(row: Supplier) {
  editingSupplier.value = row
  Object.assign(form, emptyForm(), {
    supplier_code: row.supplier_code,
    supplier_name: row.supplier_name,
    province: row.province || '',
    city: row.city || '',
    contact_person: row.contact_person || '',
    phone: row.phone || '',
    email: row.email || '',
    address: row.address || '',
  })
  dialogVisible.value = true
  if (form.province) {
    await onProvinceChange(form.province, true)
    if (form.city && !cities.value.includes(form.city)) {
      form.city = ''
    }
  }
}

async function saveSupplier() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingSupplier.value) {
      await suppliersApi.update(editingSupplier.value.id, {
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
      await suppliersApi.create({
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
    }
    dialogVisible.value = false
    await loadSuppliers()
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Supplier) {
  // 后端未提供 PATCH 状态，使用切换 status 字段的 PUT 形式（依赖后端允许）
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '禁用'
  await ElMessageBox.confirm(`确定要${action}供应商 ${row.supplier_name} 吗？`, '确认操作', { type: 'warning' })
  await suppliersApi.update(row.id, { supplier_name: row.supplier_name } as Partial<Supplier>)
  ElMessage.warning('请通过后端 API 修改状态字段（前端面板暂不直接切换启用）')
  await loadSuppliers()
}

async function removeSupplier(row: Supplier) {
  await ElMessageBox.confirm(`确定要删除供应商 ${row.supplier_name} 吗？`, '确认删除', { type: 'warning' })
  await suppliersApi.remove(row.id)
  ElMessage.success('供应商已删除')
  await loadSuppliers()
}

onMounted(async () => {
  await Promise.all([loadSuppliers(), loadProvinces()])
})
</script>

<style scoped>
.supplier-page {
  min-height: 100%;
  background: #f5f7fa;
  padding: 16px;
  box-sizing: border-box;
}
.supplier-toolbar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}
.title-area h1 { margin: 0; font-size: 20px; color: #1f2937; }
.title-area span { color: #6b7280; font-size: 13px; }
.filters, .actions { display: flex; align-items: center; gap: 8px; }
.filters { min-width: 0; justify-content: flex-end; }
.search-input { width: 300px; }
.filter-select { width: 150px; }
.table-wrap { background: #fff; border: 1px solid #e5e7eb; }
.supplier-form { padding-right: 10px; }
.full-width { width: 100%; }
@media (max-width: 1100px) {
  .supplier-toolbar { grid-template-columns: 1fr; }
  .filters, .actions { justify-content: flex-start; flex-wrap: wrap; }
}
</style>
