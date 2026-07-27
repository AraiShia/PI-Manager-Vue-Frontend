<template>
  <!-- 产品管理新增/编辑对话框组件 -->
  <el-dialog
    v-model="visible"
    :title="editingProduct ? '编辑产品' : '新增产品'"
    width="820px"
    destroy-on-close
    @closed="onClosed"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="108px"
      class="product-form"
    >
      <el-row :gutter="16">
        <!-- 客户选择框（必填） -->
        <el-col :span="12">
          <el-form-item label="客户" prop="customer_id">
            <el-select
              v-model="form.customer_id"
              filterable
              placeholder="请选择客户"
              class="full-width"
            >
              <el-option
                v-for="item in customerOptions"
                :key="item.id"
                :label="customerName(item)"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <!-- 产品类别选择框 -->
        <el-col :span="12">
          <el-form-item label="类别">
            <el-select
              v-model="form.category_id"
              clearable
              filterable
              placeholder="请选择类别"
              class="full-width"
            >
              <el-option
                v-for="item in categoryOptions"
                :key="item.code || item.id"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <!-- 基本字段输入 -->
        <el-col :span="12">
          <el-form-item label="产品名称">
            <el-input v-model="form.product_name" placeholder="请输入产品名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户型号">
            <el-input v-model="form.customer_model" placeholder="请输入客户型号" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户产品编号">
            <el-input
              v-model="codesText"
              placeholder="多个编号用逗号或换行分隔"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="OE号">
            <el-input
              v-model="oesText"
              placeholder="多个OE用逗号或换行分隔"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="品牌">
            <el-input v-model="form.brand" placeholder="请输入品牌" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="颜色">
            <el-input v-model="form.color" placeholder="请输入颜色" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="USD">
            <el-input-number
              v-model="form.price_usd"
              :min="0"
              :precision="2"
              class="full-width"
              placeholder="0.00"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="RMB">
            <el-input-number
              v-model="form.price_rmb"
              :min="0"
              :precision="2"
              class="full-width"
              placeholder="0.00"
            />
          </el-form-item>
        </el-col>

        <!-- 详细信息与大文本字段 -->
        <el-col :span="24">
          <el-form-item label="图片URL">
            <el-input v-model="form.image_url" placeholder="请输入图片URL" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="规格">
            <el-input v-model="form.specifications" placeholder="请输入产品规格" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="产品描述">
            <el-input
              v-model="form.detail_desc"
              type="textarea"
              :rows="3"
              placeholder="请输入产品描述"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="客户备注">
            <el-input
              v-model="form.customer_remark"
              type="textarea"
              :rows="2"
              placeholder="请输入客户备注"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 底部操作按钮区域 -->
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="saving" @click="saveProduct">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @file ProductManagementEditDialog.vue
 * @description 产品管理 - 新增/编辑产品独立弹窗组件
 * @author Antigravity Architect Team
 */

import { ref, reactive, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  productsApi,
  type CustomerOption,
  type CategoryOption,
  type CustomerProduct,
  type ProductFormPayload
} from '@/api/products'
import {
  FALLBACK_PARENT_CATEGORIES,
  FALLBACK_CHILD_CATEGORIES
} from '@/constants/productCategories'

/** 组件 Props 定义 */
interface Props {
  /** 外部传入的客户下拉列表（若不传则组件内部自动拉取） */
  customers?: CustomerOption[]
  /** 外部传入的类别下拉列表（若不传则组件内部自动拉取） */
  categories?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  customers: () => [],
  categories: () => []
})

/** 组件 Emits 定义 */
const emit = defineEmits<{
  /** 保存成功时触发，传递当前操作的产品对象 */
  (e: 'success', product: CustomerProduct | null): void
  /** 对话框关闭回调 */
  (e: 'closed'): void
}>()

// ================= 响应式状态声明 =================

/** 对话框显隐状态 */
const visible = ref<boolean>(false)

/** 表单提交 loading 状态 */
const saving = ref<boolean>(false)

/** 当前正在编辑的产品对象，为 null 时表示新增 */
const editingProduct = ref<CustomerProduct | null>(null)

/** 表单 Instance 引用 */
const formRef = ref<FormInstance>()

/** 客户产品编号多行/多值文本框内容 */
const codesText = ref<string>('')

/** OE号多行/多值文本框内容 */
const oesText = ref<string>('')

/** 内部自动加载的客户列表 */
const internalCustomers = ref<CustomerOption[]>([])

/** 内部自动加载的分类列表 */
const internalCategories = ref<any[]>([])

/** 空表单默认结构 */
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
  oes: []
})

/** 表单响应式数据对象 */
const form = reactive<ProductFormPayload>(emptyForm())

/** 表单校验规则 */
const rules: FormRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }]
}

// ================= 计算属性计算 =================

/** 最终使用的客户选项列表（优先使用 props） */
const customerOptions = computed<CustomerOption[]>(() => {
  return props.customers.length ? props.customers : internalCustomers.value
})

/** 最终使用的类别选项列表（优先使用 props） */
const categoryOptions = computed<any[]>(() => {
  return props.categories.length ? props.categories : internalCategories.value
})

// ================= 辅助函数定义 =================

/**
 * 格式化获取客户显示名称
 * @param item 客户选项对象
 */
function customerName(item: CustomerOption): string {
  return item.customer_name || item.name || item.customer_code || `客户#${item.id}`
}

/**
 * 将逗号/换行/分号分隔的字符串解析为干净的字符串数组
 * @param value 输入的文本字符串
 */
function splitList(value: string): string[] {
  if (!value) return []
  return value
    .split(/[\n,，;；]+/)
    .map(item => item.trim())
    .filter(Boolean)
}

/**
 * 重置/批量赋值表单字段
 * @param payload 需要覆盖赋值的数据
 */
function assignForm(payload: Partial<ProductFormPayload>): void {
  Object.assign(form, emptyForm(), payload)
}

/**
 * 如果父组件没有传递下拉选项，自动从服务端加载选项
 */
async function loadOptionsIfNeeded(): Promise<void> {
  if (!props.customers.length && internalCustomers.value.length === 0) {
    try {
      const customerRes = await productsApi.customers()
      internalCustomers.value = customerRes.data || []
    } catch (e) {
      console.error('[ProductManagementEditDialog] 获取客户下拉列表失败:', e)
    }
  }

  if (!props.categories.length && internalCategories.value.length === 0) {
    try {
      const categoryRes = await productsApi.categories()
      const cats = categoryRes.data || []
      internalCategories.value = cats.length
        ? cats
        : [...FALLBACK_PARENT_CATEGORIES, ...FALLBACK_CHILD_CATEGORIES]
    } catch (e) {
      console.error('[ProductManagementEditDialog] 获取类别下拉列表失败:', e)
      internalCategories.value = [
        ...FALLBACK_PARENT_CATEGORIES,
        ...FALLBACK_CHILD_CATEGORIES
      ]
    }
  }
}

// ================= 组件核心暴露 API 方法 =================

/**
 * 打开对话框（暴露给父组件调用）
 * @param product 若传入产品对象则为编辑模式，不传或传 null 则为新增模式
 */
async function open(product: CustomerProduct | null = null): Promise<void> {
  editingProduct.value = product
  await loadOptionsIfNeeded()

  if (product) {
    // 编辑模式：回填表单字段
    assignForm({
      customer_id: product.customer_id,
      product_name: product.product_name || '',
      customer_model: product.customer_model || '',
      color: product.color || '',
      customer_remark: product.customer_remark || '',
      category_id: product.category_id || '',
      price_usd: product.price_usd ?? null,
      price_rmb: product.price_rmb ?? null,
      detail_desc: product.detail_desc || '',
      brand: product.brand || '',
      specifications: product.specifications || '',
      image_url: product.image_url || '',
      sub_images: product.sub_images || []
    })
    codesText.value = (product.codes || []).map(item => item.product_code).join('\n')
    oesText.value = (product.oes || []).map(item => item.oe_number).join('\n')
  } else {
    // 新增模式：清空表单
    assignForm(emptyForm())
    codesText.value = ''
    oesText.value = ''
  }

  visible.value = true
}

/**
 * 关闭对话框
 */
function close(): void {
  visible.value = false
}

/**
 * 校验并保存产品数据
 */
async function saveProduct(): Promise<void> {
  if (!formRef.value) return
  await formRef.value.validate()

  saving.value = true
  try {
    const payload: ProductFormPayload = {
      ...form,
      category_id: form.category_id || null,
      codes: editingProduct.value ? undefined : splitList(codesText.value),
      oes: editingProduct.value ? undefined : splitList(oesText.value)
    }

    if (editingProduct.value) {
      await productsApi.update(editingProduct.value.id, payload)
      ElMessage.success('产品已更新')
    } else {
      await productsApi.create(payload)
      ElMessage.success('产品已创建')
    }

    const currentProduct = editingProduct.value
    close()
    emit('success', currentProduct)
  } catch (error) {
    console.error('[ProductManagementEditDialog] 保存产品失败:', error)
  } finally {
    saving.value = false
  }
}

/**
 * 对话框关闭回调
 */
function onClosed(): void {
  emit('closed')
}

// 导出供父组件调用
defineExpose({
  open,
  close
})
</script>

<style scoped>
.product-form {
  padding-right: 10px;
}

.full-width {
  width: 100%;
}
</style>
