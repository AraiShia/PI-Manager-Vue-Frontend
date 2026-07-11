<template>
  <main class="category-page">
    <section class="category-toolbar">
      <div class="title-area">
        <h1>产品类别管理</h1>
        <span>{{ allCategories.length }} 条记录</span>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增类别</el-button>
        <el-button :icon="Refresh" @click="loadCategories">刷新</el-button>
      </div>
    </section>

    <section class="table-wrap">
      <el-table
        v-loading="loading"
        :data="displayCategories"
        border
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
        empty-text="暂无类别数据"
      >
        <el-table-column prop="name" label="类别名称" min-width="200">
          <template #default="{ row }">
            <span v-if="row._isParent">{{ row.name }}</span>
            <span v-else>{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="类别代码" width="120" />
        <el-table-column label="父类别" width="150">
          <template #default="{ row }">{{ parentName(row) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openCreate(row)">添加子级</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingCategory ? '编辑类别' : '新增类别'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="类别名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="父类别" v-if="!editingCategory">
          <el-select v-model="form.parent_id" clearable filterable placeholder="顶级类别（无父类）" class="full-width">
            <el-option label="（顶级类别）" :value="null" />
            <el-option
              v-for="item in topLevelCategories"
              :key="item.code || item.id"
              :label="item.name"
              :value="item.code ?? ''"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { categoriesApi, type ProductCategory } from '@/api/categories'

const loading = ref(false)
const saving = ref(false)
const allCategories = ref<ProductCategory[]>([])
const dialogVisible = ref(false)
const editingCategory = ref<ProductCategory | null>(null)
const formRef = ref<FormInstance>()

const emptyForm = () => ({ name: '', parent_id: null as string | null, status: 1 })
const form = reactive(emptyForm())
const rules: FormRules = {
  name: [{ required: true, message: '请输入类别名称', trigger: 'blur' }],
}

const topLevelCategories = computed(() => allCategories.value.filter(item => !item.parent_id))

const displayCategories = computed(() => {
  const parents = allCategories.value.filter(item => !item.parent_id)
  return parents.map(parent => ({
    ...parent,
    _isParent: true,
    children: allCategories.value
      .filter(child => child.parent_id === parent.code)
      .map(child => ({ ...child, _isParent: false })),
  }))
})

function parentName(row: ProductCategory & { _isParent?: boolean }) {
  if (!row.parent_id) return '-'
  const parent = allCategories.value.find(item => item.code === row.parent_id)
  return parent?.name || '-'
}

async function loadCategories() {
  loading.value = true
  try {
    const res = await categoriesApi.list()
    allCategories.value = res.data || []
  } finally {
    loading.value = false
  }
}

function openCreate(parent: ProductCategory | null) {
  editingCategory.value = null
  Object.assign(form, emptyForm(), { parent_id: parent?.code ?? null })
  dialogVisible.value = true
}

function openEdit(row: ProductCategory) {
  editingCategory.value = row
  Object.assign(form, emptyForm(), {
    name: row.name,
    parent_id: row.parent_id ?? null,
    status: row.status ?? 1,
  })
  dialogVisible.value = true
}

async function saveCategory() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingCategory.value) {
      await categoriesApi.update(editingCategory.value.id, {
        name: form.name,
        parent_id: editingCategory.value.parent_id ?? null,
      })
      ElMessage.success('类别已更新')
    } else {
      await categoriesApi.create({
        name: form.name,
        parent_id: form.parent_id,
      })
      ElMessage.success('类别已创建')
    }
    dialogVisible.value = false
    await loadCategories()
  } finally {
    saving.value = false
  }
}

async function removeCategory(row: ProductCategory) {
  const hasChildren = allCategories.value.some(item => item.parent_id === row.code)
  if (hasChildren) {
    ElMessage.warning('请先删除或移动子类别')
    return
  }
  await ElMessageBox.confirm(`确定要删除类别「${row.name}」吗？`, '确认删除', { type: 'warning' })
  await categoriesApi.remove(row.id)
  ElMessage.success('类别已删除')
  await loadCategories()
}

onMounted(loadCategories)
</script>

<style scoped>
.category-page {
  min-height: 100%;
  background: #f5f7fa;
  padding: 16px;
  box-sizing: border-box;
}
.category-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}
.title-area h1 { margin: 0; font-size: 20px; color: #1f2937; }
.title-area span { color: #6b7280; font-size: 13px; }
.actions { display: flex; gap: 8px; }
.table-wrap { background: #fff; border: 1px solid #e5e7eb; }
.full-width { width: 100%; }
</style>