<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="760px"
    top="8vh"
    destroy-on-close
    class="product-supplier-url-dialog"
    :close-on-click-modal="false"
  >
    <div class="url-dialog-body">
      <!-- 关联主体卡片 -->
      <div class="context-info-bar">
        <div class="info-item">
          <span class="info-label">关联产品:</span>
          <span class="info-val product-val">{{ productName || '当前产品' }}</span>
        </div>
        <div v-if="supplierName" class="info-item">
          <span class="info-label">关联供应商:</span>
          <span class="info-val supplier-val">{{ supplierName }}</span>
        </div>
      </div>

      <!-- 新增采购链接面板 -->
      <div class="add-url-section">
        <div class="section-title">
          <span>新增采购链接 / 1688链接</span>
          <span v-if="parsedInfo.platformName" class="parsed-badge-wrap">
            <el-tag :type="parsedInfo.tagType" size="small" effect="dark">
              {{ parsedInfo.platformName }}
            </el-tag>
          </span>
        </div>
        <div class="add-url-form">
          <el-row :gutter="12">
            <el-col :span="14">
              <el-input
                v-model="newUrlForm.url"
                placeholder="请粘贴 1688 / 淘宝 / 供应商网址"
                clearable
                @input="onUrlInput"
              />
            </el-col>
            <el-col :span="10">
              <el-input
                v-model="newUrlForm.display_name"
                placeholder="网站名称 / 链接别名 (自动解析)"
                clearable
              />
            </el-col>
          </el-row>
          <div class="form-action-row mt-2">
            <el-checkbox v-model="newUrlForm.is_default">
              设为默认首选采购链接 ⭐
            </el-checkbox>
            <el-button
              type="primary"
              :loading="submitting"
              :disabled="!newUrlForm.url"
              @click="handleAddUrl"
            >
              + 保存添加采购链接
            </el-button>
          </div>
        </div>
      </div>

      <!-- 已绑定的采购链接列表 -->
      <div class="url-list-section mt-4">
        <div class="section-title list-title">
          已绑定的采购链接列表 ({{ urlList.length }})
        </div>

        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><Loading /></el-icon> 正在加载供应商链接数据...
        </div>

        <div v-else-if="urlList.length === 0" class="empty-state">
          暂无关联采购链接。请在上方输入框粘贴 1688 或供应商网址并点击保存。
        </div>

        <div v-else class="url-card-list">
          <div
            v-for="item in urlList"
            :key="item.id"
            class="url-card-item"
            :class="{ 'is-default': item.is_default }"
          >
            <!-- 头部：平台 Badge + 别名 + 默认标记 -->
            <div class="card-head">
              <div class="head-left">
                <el-tag :type="getItemTagType(item.url)" size="small">
                  {{ getItemPlatformName(item.url) }}
                </el-tag>
                <span class="url-alias font-bold">{{ item.display_name || item.supplier_name || '采购链接' }}</span>
                <el-tag v-if="item.is_default" type="warning" size="small" effect="dark" class="default-badge">
                  ⭐ 主默认链接
                </el-tag>
              </div>
              <div class="head-right">
                <span class="time-text">{{ formatDate(item.created_at) }}</span>
              </div>
            </div>

            <!-- URL 地址与跳转 -->
            <div class="card-url-row">
              <a :href="item.url" target="_blank" rel="noopener noreferrer" class="url-link">
                {{ item.url }}
              </a>
            </div>

            <!-- 操作按钮底栏 -->
            <div class="card-actions">
              <el-button
                v-if="!item.is_default"
                size="small"
                type="warning"
                plain
                @click="handleSetDefault(item)"
              >
                设为默认 ⭐
              </el-button>
              <el-button size="small" type="primary" link @click="openExternalUrl(item.url)">
                打开链接 ↗
              </el-button>
              <el-button size="small" link @click="copyUrl(item.url)">
                复制地址
              </el-button>
              <el-popconfirm
                title="确定要删除此条采购链接吗？"
                confirm-button-text="删除"
                cancel-button-text="取消"
                @confirm="handleDelete(item.id)"
              >
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @fileoverview 独立“产品-供应商-采购链接”细粒度管理对话框组件 (ProductSupplierUrlDialog.vue)
 */
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { parseShopUrl, type ParsedUrlInfo } from '@/utils/urlParser'
import { productSupplierUrlsApi, type ProductSupplierUrl } from '@/api/productSupplierUrls'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    productId: number
    productName?: string
    supplierId?: number | null
    supplierName?: string
  }>(),
  {
    modelValue: false,
    productName: '',
    supplierId: null,
    supplierName: '',
  }
)

const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  updated: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const dialogTitle = computed(() => {
  return `细粒度管理：采购链接 - ${props.productName || '产品'}`
})

const loading = ref(false)
const submitting = ref(false)
const urlList = ref<ProductSupplierUrl[]>([])

const newUrlForm = reactive({
  url: '',
  display_name: '',
  is_default: false,
})

const parsedInfo = ref<ParsedUrlInfo>({
  rawUrl: '',
  cleanUrl: '',
  platform: 'other',
  platformName: '',
  tagType: 'info',
  suggestedDisplayName: '',
})

watch(
  () => props.modelValue,
  (val) => {
    if (val && props.productId) {
      loadUrls()
      resetForm()
    }
  },
  { immediate: true }
)

function resetForm() {
  newUrlForm.url = ''
  newUrlForm.display_name = ''
  newUrlForm.is_default = urlList.value.length === 0
  parsedInfo.value = {
    rawUrl: '',
    cleanUrl: '',
    platform: 'other',
    platformName: '',
    tagType: 'info',
    suggestedDisplayName: '',
  }
}

async function loadUrls() {
  if (!props.productId) return
  loading.value = true
  try {
    const list = await productSupplierUrlsApi.list(
      props.productId,
      props.supplierId,
      props.supplierName
    )
    urlList.value = Array.isArray(list) ? list : []
    if (urlList.value.length === 0) {
      newUrlForm.is_default = true
    }
  } catch (err) {
    console.warn('获取产品采购链接失败', err)
  } finally {
    loading.value = false
  }
}

function onUrlInput(val: string) {
  if (!val) {
    parsedInfo.value.platformName = ''
    return
  }
  const info = parseShopUrl(val)
  parsedInfo.value = info

  // 若用户未手动输入 display_name，自动充填解析出的名称
  if (!newUrlForm.display_name || newUrlForm.display_name === info.suggestedDisplayName) {
    newUrlForm.display_name = info.suggestedDisplayName
  }
}

async function handleAddUrl() {
  if (!newUrlForm.url || !props.productId) return
  const info = parseShopUrl(newUrlForm.url)
  submitting.value = true

  try {
    await productSupplierUrlsApi.create({
      product_id: props.productId,
      supplier_id: props.supplierId,
      supplier_name: props.supplierName || '默认供应商',
      url: info.cleanUrl,
      display_name: newUrlForm.display_name || info.suggestedDisplayName,
      is_default: newUrlForm.is_default || urlList.value.length === 0,
    })

    ElMessage.success('成功关联保存采购链接！')
    resetForm()
    await loadUrls()
    emit('updated')
  } catch (err: any) {
    ElMessage.error(err.message || '保存采购链接失败')
  } finally {
    submitting.value = false
  }
}

async function handleSetDefault(item: ProductSupplierUrl) {
  try {
    await productSupplierUrlsApi.update(item.id, { is_default: true })
    ElMessage.success('已设置为主默认采购链接！')
    await loadUrls()
    emit('updated')
  } catch (err: any) {
    ElMessage.error('设置默认失败：' + err.message)
  }
}

async function handleDelete(id: number) {
  try {
    await productSupplierUrlsApi.remove(id)
    ElMessage.success('采购链接已删除')
    await loadUrls()
    emit('updated')
  } catch (err: any) {
    ElMessage.error('删除失败：' + err.message)
  }
}

function getItemPlatformName(url: string): string {
  return parseShopUrl(url).platformName
}

function getItemTagType(url: string) {
  return parseShopUrl(url).tagType
}

function openExternalUrl(url: string) {
  const info = parseShopUrl(url)
  window.open(info.cleanUrl, '_blank', 'noopener,noreferrer')
}

function copyUrl(url: string) {
  navigator.clipboard.writeText(url)
  ElMessage.success('链接地址已复制到剪贴板！')
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return ''
  return dateStr.replace('T', ' ').substring(0, 16)
}
</script>

<style scoped>
.url-dialog-body {
  padding: 4px;
}
.context-info-bar {
  display: flex;
  gap: 20px;
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 13px;
}
.info-label {
  color: #0369a1;
  font-weight: bold;
  margin-right: 6px;
}
.info-val {
  font-weight: 600;
  color: #0f172a;
}
.product-val { color: #0284c7; }
.supplier-val { color: #059669; }

.add-url-section {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 14px;
}
.section-title {
  font-size: 14px;
  font-weight: bold;
  color: #1e293b;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.list-title {
  color: #475569;
}
.form-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.url-card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.url-card-item {
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 14px;
  transition: all 0.2s ease;
}
.url-card-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}
.url-card-item.is-default {
  border-color: #f59e0b;
  background-color: #fffbe6;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.url-alias {
  font-size: 13px;
  color: #1e293b;
}
.time-text {
  font-size: 11px;
  color: #94a3b8;
}
.card-url-row {
  margin-bottom: 8px;
  word-break: break-all;
}
.url-link {
  font-size: 12px;
  color: #2563eb;
  text-decoration: none;
  font-family: monospace;
}
.url-link:hover {
  text-decoration: underline;
}
.card-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  border-top: 1px dashed #e2e8f0;
  padding-top: 6px;
}
.loading-state,
.empty-state {
  text-align: center;
  padding: 24px;
  color: #94a3b8;
  font-size: 13px;
}
.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
.font-bold { font-weight: bold; }
</style>
