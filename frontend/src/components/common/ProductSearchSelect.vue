<template>
  <el-select
    :model-value="selectedItem"
    filterable
    remote
    :remote-method="onQuery"
    :loading="loading"
    :placeholder="placeholder"
    :clearable="clearable"
    :disabled="disabled"
    popper-class="product-search-dropdown"
    value-key="id"
    @change="onSelect"
    @clear="onClear"
  >
    <el-option
      v-for="item in options"
      :key="item.id"
      :label="labelOf(item)"
      :value="item"
    >
      <div class="ps-item">
        <el-image
          v-if="item.image_url"
          :src="assetUrl(item.image_url)"
          class="ps-thumb"
        />
        <div v-else class="ps-thumb ps-thumb--empty">无图</div>
        <div class="ps-info">
          <!-- 产品名称 -->
          <div class="ps-line ps-name">
            <template
              v-for="(seg, i) in splitForHighlight(item.product_name, keyword)"
              :key="`n-${i}`"
            >
              <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
          <!-- 客户型号 -->
          <div v-if="item.customer_model" class="ps-line ps-model">
            <span class="ps-label">型号</span>
            <template
              v-for="(seg, i) in splitForHighlight(item.customer_model, keyword)"
              :key="`m-${i}`"
            >
              <em v-if="seg.hit" class="search-hl">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
          <!-- OE 号列表 -->
          <div v-if="item.oes.length" class="ps-line ps-oe">
            <span class="ps-label">OE</span>
            <span class="ps-oe-list">{{ item.oes.slice(0, 5).join(', ') }}</span>
          </div>
        </div>
      </div>
    </el-option>
    <!-- 空状态 -->
    <template #empty>
      <div class="ps-empty">
        <span v-if="loading">搜索中…</span>
        <span v-else-if="keyword && !options.length">未找到匹配产品</span>
        <span v-else>输入关键词搜索</span>
      </div>
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElImage } from 'element-plus'
import { splitForHighlight, type CustomerProductSearchItem } from '@/api/customerProduct'

interface Props {
  modelValue?: CustomerProductSearchItem | null
  customerId?: number
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  customerId: undefined,
  placeholder: '搜索 OE号 / 客户型号 / 产品名称',
  clearable: true,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: CustomerProductSearchItem | null): void
  (e: 'select', v: CustomerProductSearchItem): void
  (e: 'clear'): void
}>()

const selectedItem = ref(props.modelValue ?? null)
const options = ref<CustomerProductSearchItem[]>([])
const loading = ref(false)
const keyword = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null
let abortController: AbortController | null = null
let requestSeq = 0

watch(
  () => props.modelValue,
  v => {
    selectedItem.value = v ?? null
  },
)

function assetUrl(path: string | null): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const base = import.meta.env.VITE_API_BASE_URL || 'https://piapi.wakabashia.tj.cn'
  return `${base}/images/${path.replace(/^\//, '')}`
}

function labelOf(item: CustomerProductSearchItem): string {
  return item.product_name || item.customer_model || `产品 #${item.id}`
}

async function onQuery(query: string) {
  keyword.value = query
  if (searchTimer) clearTimeout(searchTimer)
  
  // 取消正在执行的请求
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  requestSeq++
  
  if (!query || query.trim().length < 1) {
    options.value = []
    loading.value = false
    return
  }
  loading.value = true
  
  const currentSeq = requestSeq
  
  searchTimer = setTimeout(async () => {
    abortController = new AbortController()
    try {
      const { searchCustomerProducts } = await import('@/api/customerProduct')
      const results = await searchCustomerProducts({
        keyword: query.trim(),
        customerId: props.customerId,
        limit: 20,
      })
      // 检查是否是最新请求，避免旧请求覆盖新结果
      if (currentSeq === requestSeq) {
        options.value = results
      }
    } catch {
      if (currentSeq === requestSeq) {
        options.value = []
      }
    } finally {
      if (currentSeq === requestSeq) {
        loading.value = false
      }
    }
  }, 150)
}

function onSelect(item: CustomerProductSearchItem) {
  selectedItem.value = item
  emit('update:modelValue', item)
  emit('select', item)
}

function onClear() {
  // 取消正在执行的请求，避免清空后旧请求覆盖结果
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  requestSeq++
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
  
  selectedItem.value = null
  options.value = []
  keyword.value = ''
  loading.value = false
  emit('update:modelValue', null)
  emit('clear')
}
</script>

<style scoped>
.ps-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 6px;
  min-height: 64px;
}

.ps-thumb {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid #eee;
}

.ps-thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #999;
  font-size: 11px;
}

.ps-info {
  flex: 1;
  min-width: 0;
}

.ps-line {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 13px;
  line-height: 1.8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px 0;
}

.ps-name {
  font-weight: 500;
  color: #303133;
}

.ps-model {
  color: #606266;
}

.ps-oe {
  color: #909399;
  font-size: 12px;
}

.ps-label {
  color: #c0c4cc;
  font-size: 11px;
  flex-shrink: 0;
}

.ps-oe-list {
  overflow: hidden;
  text-overflow: ellipsis;
}

:global(.product-search-dropdown .el-select-dropdown__item) {
  height: auto !important;
  padding: 0 !important;
  line-height: normal !important;
}

:deep(.search-hl) {
  font-style: normal;
  background: #fde2e2;
  color: #c0392b;
  border-radius: 2px;
  padding: 0 1px;
}

.ps-empty {
  padding: 12px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>
