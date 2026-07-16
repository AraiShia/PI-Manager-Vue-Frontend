<template>
  <main class="product-page">
    <section class="product-toolbar">
      <div class="title-area">
        <h1>产品列表</h1>
        <span>{{ total }} 条记录</span>
      </div>
      <div class="filters">
        <el-input
          v-model="filters.search"
          clearable
          class="search-input"
          placeholder="搜索 OE号/产品编号/系统编号/品牌/描述"
          @keyup.enter="loadProducts(1)"
        />
        <el-select v-model="filters.categoryLevel1" clearable filterable placeholder="全部大类" class="filter-select" @change="onCategoryLevel1Change">
          <el-option v-for="item in parentCategories" :key="item.code" :label="item.name" :value="item.code" />
        </el-select>
        <el-select v-model="filters.categoryLevel2" clearable filterable placeholder="全部子类" class="filter-select" :disabled="!filters.categoryLevel1" @change="onCategoryLevel2Change">
          <el-option v-for="item in childCategoryOptions" :key="item.code" :label="item.name" :value="item.code" />
        </el-select>
        <el-select v-model="filters.customerId" clearable filterable placeholder="全部客户" class="filter-select">
          <el-option v-for="item in customers" :key="item.id" :label="customerName(item)" :value="item.id" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="loadProducts(1)">搜索</el-button>
        <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增产品</el-button>
        <el-button :icon="Upload" disabled>批量导入</el-button>
        <el-button :icon="Refresh" @click="loadProducts(page)">刷新</el-button>
      </div>
    </section>

    <section class="table-wrap">
      <el-table
        v-loading="loading"
        :data="products"
        height="calc(100vh - 210px)"
        border
        row-key="id"
        empty-text="暂无产品数据"
        @selection-change="selectedRows = $event"
        @row-dblclick="openEdit"
      >
        <el-table-column type="selection" width="42" fixed />
        <el-table-column prop="primary_code" label="客户产品编号" width="130" show-overflow-tooltip />
        <el-table-column label="系统编号" width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ shortSystemCode(row.system_code) }}</template>
        </el-table-column>
        <el-table-column label="OE号" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-if="(row.oes?.length || 0) > 1" size="small" type="primary">多OE号</el-tag>
            <span v-else>{{ row.primary_oe || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="图片" width="82" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              class="product-image"
              fit="contain"
              :src="assetUrl(row.image_url)"
              :preview-src-list="imageList(row)"
              preview-teleported
            />
            <span v-else class="muted">暂无图片</span>
          </template>
        </el-table-column>
        <el-table-column label="产品名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.product_name || row.detail_desc || '-' }}</template>
        </el-table-column>
        <el-table-column prop="customer_model" label="客户型号" width="120" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户" width="130" show-overflow-tooltip />
        <el-table-column prop="category_name" label="类别" width="110" show-overflow-tooltip />
        <el-table-column prop="color" label="颜色" width="90" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="100" show-overflow-tooltip />
        <el-table-column label="USD" width="95" align="right">
          <template #default="{ row }">{{ formatUsd(row.price_usd) }}</template>
        </el-table-column>
        <el-table-column label="RMB" width="95" align="right">
          <template #default="{ row }">{{ formatRmb(row.price_rmb) }}</template>
        </el-table-column>
        <el-table-column prop="specifications" label="规格" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteProduct(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="batch-actions">
          <el-button :disabled="!selectedRows.length" @click="batchDisable">批量禁用</el-button>
          <el-button type="danger" :disabled="!selectedRows.length" @click="batchDelete">批量删除</el-button>
        </div>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[50, 100, 200, 500]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadProducts"
          @size-change="onPageSizeChange"
        />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingProduct ? '编辑产品' : '新增产品'" width="820px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="108px" class="product-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_id">
              <el-select v-model="form.customer_id" filterable placeholder="请选择客户" class="full-width">
                <el-option v-for="item in customers" :key="item.id" :label="customerName(item)" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类别">
              <el-select v-model="form.category_id" clearable filterable placeholder="请选择类别" class="full-width">
                <el-option v-for="item in categories" :key="item.code || item.id" :label="item.name" :value="item.code" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12"><el-form-item label="产品名称"><el-input v-model="form.product_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="客户型号"><el-input v-model="form.customer_model" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="客户产品编号"><el-input v-model="codesText" placeholder="多个编号用逗号或换行分隔" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="OE号"><el-input v-model="oesText" placeholder="多个OE用逗号或换行分隔" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="品牌"><el-input v-model="form.brand" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="颜色"><el-input v-model="form.color" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="USD"><el-input-number v-model="form.price_usd" :min="0" :precision="2" class="full-width" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="RMB"><el-input-number v-model="form.price_rmb" :min="0" :precision="2" class="full-width" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="图片URL"><el-input v-model="form.image_url" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="规格"><el-input v-model="form.specifications" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="产品描述"><el-input v-model="form.detail_desc" type="textarea" :rows="3" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="客户备注"><el-input v-model="form.customer_remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { assetUrl } from '@/api/base'
import { productsApi, type CategoryOption, type CustomerOption, type CustomerProduct, type ProductFormPayload } from '@/api/products'
import { FALLBACK_PARENT_CATEGORIES, FALLBACK_CHILD_CATEGORIES } from '@/constants/productCategories'

const loading = ref(false)
const saving = ref(false)
const products = ref<CustomerProduct[]>([])
const customers = ref<CustomerOption[]>([])
const categories = ref<any[]>([])
const selectedRows = ref<CustomerProduct[]>([])
const page = ref(1)
const pageSize = ref(100)
const total = ref(0)
const dialogVisible = ref(false)
const editingProduct = ref<CustomerProduct | null>(null)
const formRef = ref<FormInstance>()
const codesText = ref('')
const oesText = ref('')

const filters = reactive({
  search: '',
  customerId: undefined as number | undefined,
  categoryLevel1: undefined as string | undefined,
  categoryLevel2: undefined as string | undefined,
})

const parentCategories = computed(() =>
  categories.value.filter(c => !c.parent_id)
)

const childCategoryOptions = computed(() =>
  categories.value.filter(c => c.parent_id === filters.categoryLevel1)
)

function onCategoryLevel1Change() {
  filters.categoryLevel2 = undefined
}

function onCategoryLevel2Change() {
  // 子类变化时无需额外处理
}

const emptyForm = (): ProductFormPayload => ({
  customer_id: undefined as unknown as number,
  product_name: '',
  customer_model: '',
  color: '',
  customer_remark: '',
  category_id: '',
  price_usd: null,
  price_rmb: null,
  detail_desc: '',
  brand: '',
  specifications: '',
  image_url: '',
  codes: [],
  oes: [],
})

const form = reactive<ProductFormPayload>(emptyForm())
const rules: FormRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
}

const categoryMap = computed(() => new Map(categories.value.map(item => [item.code, item.name])))

function customerName(item: CustomerOption) {
  return item.customer_name || item.name || item.customer_code || `客户#${item.id}`
}

function shortSystemCode(value?: string | null) {
  if (!value) return '-'
  return value.length >= 9 ? value.slice(-9) : value
}

function formatUsd(value?: number | null) {
  return value ? `$${Number(value).toFixed(2)}` : '-'
}

function formatRmb(value?: number | null) {
  return value ? `¥${Number(value).toFixed(2)}` : '-'
}

function imageList(row: CustomerProduct) {
  return [row.image_url, ...(row.sub_images || [])].filter(Boolean).map(item => assetUrl(item!))
}

function splitList(value: string) {
  return value.split(/[\n,，;；]+/).map(item => item.trim()).filter(Boolean)
}

function assignForm(payload: ProductFormPayload) {
  Object.assign(form, emptyForm(), payload)
}

async function loadOptions() {
  const [customerRes, categoryRes] = await Promise.all([
    productsApi.customers(),
    productsApi.categories(),
  ])
  customers.value = customerRes.data || []
  const cats = categoryRes.data || []
  categories.value = cats.length ? cats : [
    ...FALLBACK_PARENT_CATEGORIES,
    ...FALLBACK_CHILD_CATEGORIES,
  ]
}

async function loadProducts(nextPage = page.value) {
  loading.value = true
  try {
    page.value = nextPage
    // 只传叶子类目码（子类选中时）或大类码
    const category_code = filters.categoryLevel2 || filters.categoryLevel1
    const res = await productsApi.list({
      page: page.value,
      page_size: pageSize.value,
      search: filters.search || undefined,
      customer_id: filters.customerId,
      category_code: category_code || undefined,
    })
    products.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.search = ''
  filters.customerId = undefined
  filters.categoryLevel1 = undefined
  filters.categoryLevel2 = undefined
  loadProducts(1)
}

function onPageSizeChange() {
  loadProducts(1)
}

function openCreate() {
  editingProduct.value = null
  assignForm(emptyForm())
  codesText.value = ''
  oesText.value = ''
  dialogVisible.value = true
}

function openEdit(row: CustomerProduct) {
  editingProduct.value = row
  assignForm({
    customer_id: row.customer_id,
    product_name: row.product_name || '',
    customer_model: row.customer_model || '',
    color: row.color || '',
    customer_remark: row.customer_remark || '',
    category_id: row.category_id || '',
    price_usd: row.price_usd ?? null,
    price_rmb: row.price_rmb ?? null,
    detail_desc: row.detail_desc || '',
    brand: row.brand || '',
    specifications: row.specifications || '',
    image_url: row.image_url || '',
    sub_images: row.sub_images || [],
  })
  codesText.value = (row.codes || []).map(item => item.product_code).join('\n')
  oesText.value = (row.oes || []).map(item => item.oe_number).join('\n')
  dialogVisible.value = true
}

async function saveProduct() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: ProductFormPayload = {
      ...form,
      category_id: form.category_id || null,
      codes: editingProduct.value ? undefined : splitList(codesText.value),
      oes: editingProduct.value ? undefined : splitList(oesText.value),
    }
    if (editingProduct.value) {
      await productsApi.update(editingProduct.value.id, payload)
      ElMessage.success('产品已更新')
    } else {
      await productsApi.create(payload)
      ElMessage.success('产品已创建')
    }
    dialogVisible.value = false
    await loadProducts(page.value)
  } finally {
    saving.value = false
  }
}

async function deleteProduct(row: CustomerProduct) {
  await ElMessageBox.confirm(`确定要删除产品 ${row.system_code || row.primary_code || row.product_name || row.id} 吗？`, '确认删除', { type: 'warning' })
  await productsApi.remove(row.id)
  ElMessage.success('产品已删除')
  await loadProducts(page.value)
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定要删除选中的 ${selectedRows.value.length} 个产品吗？`, '确认删除', { type: 'warning' })
  for (const row of selectedRows.value) await productsApi.remove(row.id)
  ElMessage.success('批量删除完成')
  await loadProducts(page.value)
}

async function batchDisable() {
  await ElMessageBox.confirm(`确定要禁用选中的 ${selectedRows.value.length} 个产品吗？`, '确认操作', { type: 'warning' })
  for (const row of selectedRows.value) await productsApi.update(row.id, { is_active: false })
  ElMessage.success('批量禁用完成')
  await loadProducts(page.value)
}

onMounted(async () => {
  await loadOptions()
  await loadProducts(1)
})
</script>

<style scoped>
.product-page {
  min-height: 100%;
  background: #f5f7fa;
  padding: 16px;
  box-sizing: border-box;
}
.product-toolbar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}
.title-area h1 {
  margin: 0;
  font-size: 20px;
  color: #1f2937;
}
.title-area span {
  color: #6b7280;
  font-size: 13px;
}
.filters,
.actions,
.table-footer,
.batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filters {
  min-width: 0;
  justify-content: flex-end;
}
.search-input {
  width: 300px;
}
.filter-select {
  width: 150px;
}
.table-wrap {
  background: #fff;
  border: 1px solid #e5e7eb;
}
.product-image {
  width: 56px;
  height: 56px;
  border: 1px solid #e5e7eb;
  background: #fff;
}
.muted {
  color: #9ca3af;
  font-size: 12px;
}
.table-footer {
  justify-content: space-between;
  padding: 10px 12px;
}
.product-form {
  padding-right: 10px;
}
.full-width {
  width: 100%;
}
@media (max-width: 1100px) {
  .product-toolbar {
    grid-template-columns: 1fr;
  }
  .filters,
  .actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
