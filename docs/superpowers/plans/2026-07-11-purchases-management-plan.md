# 采购订单管理页面实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现 `/purchases` 采购订单列表页，替换占位页，支持列表加载、状态筛选、确认/入库操作、发票查看、合同导出。

**架构：** 复用现有 `purchase.ts` API，扩展 `list`/`confirm`/`inbound`/`exportContract`/`getInvoiceUrl`；新建 `PurchaseManagement.vue` 单文件页面，复用 `el-table`/`el-pagination` 模式；状态在组件内管理（不需要独立 store）。

**技术栈：** Vue 3 + TypeScript + Element Plus + Axios

---

## 文件结构

- 创建：`frontend/src/views/purchase/PurchaseManagement.vue` — 采购管理页面
- 修改：`frontend/src/api/purchase.ts` — 扩展 API 方法
- 修改：`frontend/src/router/index.ts` — 注册 `/purchases` 路由
- 修改：`frontend/src/router/businessRoutes.ts` — `implemented: true`

---

## 任务 1：扩展 API 方法

**文件：**
- 修改：`frontend/src/api/purchase.ts`

- [ ] **步骤 1：添加 PurchaseListResponse 类型**

在文件顶部 `PurchaseItem` 类型声明之后，添加：

```typescript
export interface PurchaseListResponse {
  data: PurchaseOrderSummary[]
  total: number
}

export interface PurchaseOrderSummary {
  id: number
  po_no: string
  pi_id: number
  pi_no: string
  supplier_id: number
  supplier_name: string
  total_amount: number
  currency: string
  status: number
  created_at: string
}
```

- [ ] **步骤 2：在 `purchaseApi` 对象中追加 5 个方法**

在现有 `purchaseApi` 的 `updatePiItemLink` 方法之后添加：

```typescript
list: (params: { page?: number; page_size?: number; keyword?: string; status?: number }) =>
  client.get<ApiResponse<PurchaseListResponse>>('/api/purchase-orders', { params }),

confirm: (id: number) =>
  client.post<ApiResponse<void>>(`/api/purchase-orders/${id}/confirm`),

inbound: (id: number) =>
  client.post<ApiResponse<void>>(`/api/purchase-orders/${id}/inbound`),

exportContract: (id: number) =>
  client.get(`/api/export/purchase/${id}/contract`, { responseType: 'blob' }),

getInvoiceUrl: (id: number) =>
  client.get<ApiResponse<{ url?: string }>>(`/api/purchase-orders/${id}/invoice`),
```

- [ ] **步骤 3：运行自动类型检查**

运行：`cd frontend && npx tsc --noEmit`
预期：无编译错误，exit 0

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/api/purchase.ts
git commit -m "feat(purchase): 扩展 API list/confirm/inbound/exportContract/getInvoiceUrl"
```

---

## 任务 2：创建采购管理页面

**文件：**
- 创建：`frontend/src/views/purchase/PurchaseManagement.vue`

- [ ] **步骤 1：创建页面文件**

创建 `frontend/src/views/purchase/PurchaseManagement.vue`，内容如下（完整模板）：

```vue
<template>
  <div class="purchase-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索采购单号 / PI号 / 供应商"
          clearable
          style="width: 240px"
          @keyup.enter="loadData"
        />
        <el-select v-model="status" placeholder="状态" clearable style="width: 120px; margin-left: 8px">
          <el-option label="草稿" :value="1" />
          <el-option label="已确认" :value="2" />
          <el-option label="已入库" :value="3" />
        </el-select>
        <el-button type="primary" style="margin-left: 8px" :loading="loading" @click="loadData">搜索</el-button>
      </div>
      <div class="toolbar-right">
        <el-button :loading="loading" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <el-table :data="list" v-loading="loading" stripe class="purchase-table">
      <el-table-column prop="po_no" label="采购单号" min-width="140" />
      <el-table-column prop="pi_no" label="PI号" min-width="120" />
      <el-table-column prop="supplier_name" label="供应商" min-width="140" />
      <el-table-column label="金额" min-width="100">
        <template #default="{ row }">
          {{ row.total_amount }} {{ row.currency }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 1"
            type="success"
            size="small"
            link
            :loading="row._confirming"
            @click="onConfirm(row)"
          >确认</el-button>
          <el-button
            v-if="row.status === 2"
            type="warning"
            size="small"
            link
            :loading="row._inbounding"
            @click="onInbound(row)"
          >入库</el-button>
          <el-button
            type="info"
            size="small"
            link
            @click="onViewInvoice(row)"
          >发票</el-button>
          <el-button
            type="primary"
            size="small"
            link
            :loading="row._exporting"
            @click="onExportContract(row)"
          >合同</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { purchaseApi, type PurchaseOrderSummary } from '@/api/purchase'

const loading = ref(false)
const list = ref<PurchaseOrderSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const status = ref<number | undefined>(undefined)

function statusLabel(s: number) {
  return { 1: '草稿', 2: '已确认', 3: '已入库' }[s] ?? '未知'
}

function statusType(s: number) {
  return { 1: 'info', 2: 'warning', 3: 'success' }[s] as any
}

async function loadData() {
  loading.value = true
  try {
    const res = await purchaseApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: status.value,
    })
    list.value = (res.data?.data || []).map(item => ({
      ...item,
      _confirming: false,
      _inbounding: false,
      _exporting: false,
    }))
    total.value = res.data?.total || 0
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function onConfirm(row: any) {
  row._confirming = true
  try {
    await purchaseApi.confirm(row.id)
    ElMessage.success('确认成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '确认失败')
  } finally {
    row._confirming = false
  }
}

async function onInbound(row: any) {
  row._inbounding = true
  try {
    await purchaseApi.inbound(row.id)
    ElMessage.success('入库成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '入库失败')
  } finally {
    row._inbounding = false
  }
}

async function onViewInvoice(row: any) {
  try {
    const res = await purchaseApi.getInvoiceUrl(row.id)
    const url = res.data?.data?.url
    if (url) {
      window.open(url, '_blank')
    } else {
      ElMessage.info('暂无发票')
    }
  } catch (e: any) {
    ElMessage.info('暂无发票')
  }
}

async function onExportContract(row: any) {
  row._exporting = true
  try {
    const res = await purchaseApi.exportContract(row.id)
    const blob = res.data as unknown as Blob
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = `Contract_${row.po_no}.xlsx`
    a.click()
    URL.revokeObjectURL(objectUrl)
    ElMessage.success('合同已导出')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '导出失败')
  } finally {
    row._exporting = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.purchase-page {
  padding: 16px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
}
.purchase-table {
  width: 100%;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
```

- [ ] **步骤 2：运行构建验证**

运行：`cd frontend && npm run build`
预期：exit 0，无编译错误

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/views/purchase/PurchaseManagement.vue
git commit -m "feat(purchase): 实现采购订单列表页面"
```

---

## 任务 3：注册路由

**文件：**
- 修改：`frontend/src/router/index.ts`
- 修改：`frontend/src/router/businessRoutes.ts`

- [ ] **步骤 1：在 `implementedRoutes` 中注册路由**

在 `router/index.ts` 中找到 `implementedRoutes` 数组，在 `/shipments` 之后添加：

```typescript
{ path: '/purchases', name: 'Purchases', component: () => import('@/views/purchase/PurchaseManagement.vue') },
```

- [ ] **步骤 2：将 purchase 改为 implemented: true**

在 `businessRoutes.ts` 中找到 purchase 条目，将 `implemented: false` 改为 `implemented: true`。

- [ ] **步骤 3：运行构建验证**

运行：`cd frontend && npm run build`
预期：exit 0

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/router/index.ts frontend/src/router/businessRoutes.ts
git commit -m "feat(router): 注册 /purchases 路由并标记为已实现"
```

---

## 任务 4：手动验收

打开浏览器访问 `http://localhost:5173/purchases`（或 PyQt 客户端点击“采购管理”菜单），逐一验证：

- [ ] 采购订单列表正常加载
- [ ] 状态着色正确（草稿灰、已确认橙、已入库绿）
- [ ] 搜索框输入关键词能过滤列表
- [ ] 状态筛选下拉能过滤列表
- [ ] 确认按钮点击后状态更新为"已确认"
- [ ] 入库按钮点击后状态更新为"已入库"
- [ ] 发票按钮能打开/预览发票（无发票时显示"暂无发票"）
- [ ] 合同按钮能下载 Excel
- [ ] 刷新按钮能重新加载列表
