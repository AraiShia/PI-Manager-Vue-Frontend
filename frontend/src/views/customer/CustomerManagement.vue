<template>
  <main class="customer-page">
    <section class="customer-toolbar">
      <div class="title-area">
        <h1>客户管理</h1>
        <span>{{ filteredCustomers.length }} 条记录</span>
      </div>
      <div class="filters">
        <el-input v-model="filters.search" clearable class="search-input" placeholder="搜索客户编号/名称/国家" @keyup.enter="applyFilters" />
        <el-select v-model="filters.deptId" clearable placeholder="全部部门" class="filter-select">
          <el-option v-for="d in deptOptions" :key="d.value" :label="d.label" :value="d.value" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="applyFilters">搜索</el-button>
        <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增客户</el-button>
        <el-button :icon="Refresh" @click="loadCustomers">刷新</el-button>
      </div>
    </section>

    <section class="table-wrap">
      <el-table
        v-loading="loading"
        :data="filteredCustomers"
        border
        height="calc(100vh - 210px)"
        row-key="id"
        empty-text="暂无客户数据"
      >
        <el-table-column prop="customer_code" label="客户编号" width="130" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="部门" width="90" align="center">
          <template #default="{ row }">{{ deptLabel(row.dept_id) }}</template>
        </el-table-column>
        <el-table-column prop="country" label="国家" width="110" show-overflow-tooltip />
        <el-table-column prop="payment_terms" label="付款条款" width="120" show-overflow-tooltip />
        <el-table-column prop="special_require" label="特殊要求" min-width="200" show-overflow-tooltip />
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
            <el-button link type="danger" @click="removeCustomer(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingCustomer ? '编辑客户' : '新增客户'"
      width="780px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="customer-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="部门">
              <el-select v-model="form.dept_id" class="full-width">
                <el-option v-for="d in deptOptions" :key="d.value" :label="d.label" :value="d.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户编号">
              <el-input v-model="form.customer_code" placeholder="留空自动生成" :disabled="!!editingCustomer" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-input v-model="form.customer_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家">
              <el-input v-model="form.country" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="付款条款">
              <el-input v-model="form.payment_terms" placeholder="如 T/T 30天" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="基本要求">
              <el-input v-model="form.basic_require" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="特殊要求">
              <el-input v-model="form.special_require" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">联系人</el-divider>

        <el-table :data="formContacts" border size="small" empty-text="暂无联系人">
          <el-table-column label="姓名" min-width="120">
            <template #default="{ row }"><el-input v-model="row.name" /></template>
          </el-table-column>
          <el-table-column label="电话" min-width="120">
            <template #default="{ row }"><el-input v-model="row.phone" /></template>
          </el-table-column>
          <el-table-column label="邮箱" min-width="160">
            <template #default="{ row }"><el-input v-model="row.email" /></template>
          </el-table-column>
          <el-table-column label="职位" min-width="120">
            <template #default="{ row }"><el-input v-model="row.position" /></template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" @click="formContacts.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="contact-actions">
          <el-button :icon="Plus" @click="formContacts.push({ name: '', phone: '', email: '', position: '' })">添加联系人</el-button>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCustomer">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { customersApi, type Customer, type CustomerContact } from '@/api/customers'

const loading = ref(false)
const saving = ref(false)
const customers = ref<Customer[]>([])
const dialogVisible = ref(false)
const editingCustomer = ref<Customer | null>(null)
const formRef = ref<FormInstance>()
const formContacts = ref<CustomerContact[]>([])

const deptOptions = [
  { value: 'S', label: 'S - 索英普' },
  { value: 'W', label: 'W - 维那' },
  { value: 'M', label: 'M - 马迪那' },
  { value: 'D', label: 'D - 银达' },
]

const filters = reactive({
  search: '',
  deptId: undefined as string | undefined,
})

const emptyForm = () => ({
  customer_code: '',
  customer_name: '',
  dept_id: 'S',
  country: '',
  payment_terms: '',
  basic_require: '',
  special_require: '',
})

const form = reactive(emptyForm())

const rules: FormRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
}

const filteredCustomers = computed(() => {
  const keyword = filters.search.trim().toLowerCase()
  return customers.value.filter(item => {
    if (filters.deptId && item.dept_id !== filters.deptId) return false
    if (!keyword) return true
    return [item.customer_code, item.customer_name, item.country].some(
      value => typeof value === 'string' && value.toLowerCase().includes(keyword)
    )
  })
})

function deptLabel(value?: string | null) {
  const match = deptOptions.find(d => d.value === value)
  return match ? match.label.split(' - ')[0] : '-'
}

async function loadCustomers() {
  loading.value = true
  try {
    const res = await customersApi.list({ limit: 1000 })
    customers.value = res.data || []
  } finally {
    loading.value = false
  }
}

function applyFilters() { /* computed handles it */ }

function resetFilters() {
  filters.search = ''
  filters.deptId = undefined
}

function openCreate() {
  editingCustomer.value = null
  Object.assign(form, emptyForm())
  formContacts.value = []
  dialogVisible.value = true
}

async function openEdit(row: Customer) {
  editingCustomer.value = row
  Object.assign(form, emptyForm(), {
    customer_code: row.customer_code || '',
    customer_name: row.customer_name || '',
    dept_id: row.dept_id || 'S',
    country: row.country || '',
    payment_terms: row.payment_terms || '',
    basic_require: row.basic_require || '',
    special_require: row.special_require || '',
  })
  formContacts.value = []
  dialogVisible.value = true
  try {
    const res = await customersApi.contacts(row.id)
    formContacts.value = (res.data || []).map(item => ({ ...item }))
  } catch (err) {
    console.warn('[客户] 加载联系人失败', err)
  }
}

async function saveCustomer() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingCustomer.value) {
      await customersApi.update(editingCustomer.value.id, {
        customer_name: form.customer_name,
        dept_id: form.dept_id,
        country: form.country || null,
        payment_terms: form.payment_terms || null,
        basic_require: form.basic_require || null,
        special_require: form.special_require || null,
      })
      await syncContacts(editingCustomer.value.id)
      ElMessage.success('客户已更新')
    } else {
      const res = await customersApi.create({
        customer_name: form.customer_name,
        dept_id: form.dept_id,
        country: form.country || null,
        payment_terms: form.payment_terms || null,
        basic_require: form.basic_require || null,
        special_require: form.special_require || null,
      })
      const newId = res.data?.id
      if (newId) await syncContacts(newId)
      ElMessage.success('客户已创建')
    }
    dialogVisible.value = false
    await loadCustomers()
  } finally {
    saving.value = false
  }
}

async function syncContacts(customerId: number) {
  const desired = formContacts.value
    .filter(item => (item.name || '').trim() || (item.phone || '').trim() || (item.email || '').trim())
    .map(item => ({
      name: item.name?.trim() || null,
      phone: item.phone?.trim() || null,
      email: item.email?.trim() || null,
      position: item.position?.trim() || null,
    }))
  try {
    const existing = (await customersApi.contacts(customerId)).data || []
    const desiredKey = JSON.stringify({ name: desired.map(d => d.name) })
    const existingKey = JSON.stringify({ name: existing.map(e => e.name) })
    if (desiredKey === existingKey && desired.length === existing.length) return
    for (const item of existing) {
      if (item.id) await customersApi.removeContact(customerId, item.id)
    }
    for (const item of desired) {
      await customersApi.createContact(customerId, item)
    }
  } catch (err) {
    console.warn('[客户] 同步联系人失败', err)
  }
}

async function toggleStatus(row: Customer) {
  const action = row.status === 1 ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定要${action}客户 ${row.customer_name} 吗？`, '确认操作', { type: 'warning' })
  await customersApi.toggleStatus(row.id)
  ElMessage.success('状态已更新')
  await loadCustomers()
}

async function removeCustomer(row: Customer) {
  await ElMessageBox.confirm(`确定要删除客户 ${row.customer_name} 吗？`, '确认删除', { type: 'warning' })
  await customersApi.remove(row.id)
  ElMessage.success('客户已删除')
  await loadCustomers()
}

onMounted(loadCustomers)
</script>

<style scoped>
.customer-page {
  min-height: 100%;
  background: #f5f7fa;
  padding: 16px;
  box-sizing: border-box;
}
.customer-toolbar {
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
.search-input { width: 280px; }
.filter-select { width: 140px; }
.table-wrap {
  background: #fff;
  border: 1px solid #e5e7eb;
}
.customer-form { padding-right: 10px; }
.full-width { width: 100%; }
.contact-actions { margin-top: 10px; }
@media (max-width: 1100px) {
  .customer-toolbar { grid-template-columns: 1fr; }
  .filters, .actions { justify-content: flex-start; flex-wrap: wrap; }
}
</style>