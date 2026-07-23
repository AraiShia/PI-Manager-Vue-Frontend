<template>
  <el-select
    :model-value="selectedItem"
    filterable
    remote
    :remote-method="onQuery"
    :loading="loading"
    :placeholder="currentName || placeholder"
    :clearable="clearable"
    :disabled="disabled"
    popper-class="supplier-search-dropdown"
    value-key="id"
    @change="onSelect"
    @clear="onClear"
    @visible-change="onVisibleChange"
  >
    <el-option
      v-for="item in computedOptions"
      :key="item.id"
      :label="labelOf(item)"
      :value="item"
    >
      <div class="ss-item">
        <div class="ss-info">
          <div class="ss-line ss-name">
            <span>{{ item.supplier_name }}</span>
          </div>
          <div v-if="item.supplier_code" class="ss-line ss-code">
            <span class="ss-label">编号</span>
            <span>{{ item.supplier_code }}</span>
          </div>
          <div v-if="item.contact_person || item.phone" class="ss-line ss-contact">
            <span v-if="item.contact_person">{{ item.contact_person }}</span>
            <span v-if="item.contact_person && item.phone"> · </span>
            <span v-if="item.phone">{{ item.phone }}</span>
          </div>
        </div>
      </div>
    </el-option>
    <!-- 空状态 -->
    <template #empty>
      <div class="ss-empty">
        <span v-if="loading">搜索中…</span>
        <span v-else-if="keyword && !options.length">未找到匹配供应商</span>
        <span v-else>输入关键词搜索</span>
      </div>
      <slot name="empty-extra" :keyword="keyword" />
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { suppliersApi, type Supplier } from '@/api/suppliers'

interface Props {
  modelValue?: Supplier | null
  /** 当前供应商名称（modelValue 为空时兜底显示） */
  currentName?: string
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  currentName: '',
  placeholder: '搜索或选择供应商',
  clearable: true,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: Supplier | null): void
  (e: 'select', v: Supplier): void
  (e: 'clear'): void
}>()

const selectedItem = ref(props.modelValue ?? null)
const options = ref<Supplier[]>([])
const computedOptions = computed(() => {
  const opts = [...options.value]
  if (selectedItem.value && !opts.some(o => o.id === selectedItem.value!.id)) {
    opts.unshift(selectedItem.value)
  }
  return opts
})
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

function labelOf(item: Supplier): string {
  return item.supplier_name || `供应商 #${item.id}`
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

  // 空关键词时加载前 20 条供应商（支持下拉直接选择）
  if (!query || query.trim().length < 1) {
    loading.value = true
    const currentSeq = requestSeq
    searchTimer = setTimeout(async () => {
      abortController = new AbortController()
      try {
        const res = await suppliersApi.list({ skip: 0, limit: 50 })
        if (currentSeq === requestSeq) {
          options.value = res.data || []
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
    }, 300)
    return
  }

  loading.value = true
  const currentSeq = requestSeq

  searchTimer = setTimeout(async () => {
    abortController = new AbortController()
    try {
      const res = await suppliersApi.list({ skip: 0, limit: 20, keyword: query.trim() })
      if (currentSeq === requestSeq) {
        options.value = res.data || []
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
  }, 300)
}

function onSelect(item: Supplier) {
  selectedItem.value = item
  emit('update:modelValue', item)
  emit('select', item)
}

function onClear() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
  requestSeq++

  selectedItem.value = null
  keyword.value = ''
  // 清空后重新加载初始列表（支持下拉直接选）
  onQuery('')
  emit('update:modelValue', null)
  emit('clear')
}

function onVisibleChange(visible: boolean) {
  // 打开下拉时主动加载初始列表（解决首次打开 remote-method 不触发的问题）
  if (visible && options.value.length === 0 && !loading.value) {
    onQuery('')
  }
}

onBeforeUnmount(() => {
  // 组件卸载时取消所有待发请求和定时器
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
})
</script>

<style scoped>
.ss-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
  min-height: 56px;
  box-sizing: border-box;
}

.ss-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ss-line {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 13px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 1px 0;
}

.ss-name {
  font-weight: 500;
  color: #303133;
}

.ss-code {
  color: #606266;
  font-size: 12px;
}

.ss-contact {
  color: #909399;
  font-size: 12px;
}

.ss-label {
  color: #c0c4cc;
  font-size: 11px;
  flex-shrink: 0;
}

:global(.supplier-search-dropdown .el-select-dropdown__item) {
  height: auto !important;
  padding: 0 !important;
  line-height: normal !important;
}

.ss-empty {
  padding: 12px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>
