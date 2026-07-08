# 议价沟通历史与报价单导出 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。
>
> **注意：** 本计划不含数据库迁移任务，请手动执行迁移或在数据库管理员协助下完成。

**目标：** 在 PI 明细行支持议价多轮沟通历史持久化（JSON 列），前端通过 NegotiationDialog 编辑；同时新增报价单导出功能展示沟通历史。

**架构：** `PiProformaInvoiceItem` 新增 `negotiation_history`（JSON）、`confirm_info`（Text）、`quote_remark`（Text）三列；`update_pi_item` 和 BFF 层适配读写；前端新增 `NegotiationDialog.vue`，双击列触发；报价单通过新建 `QuoteExporter` 导出并展示完整谈判历史。

**技术栈：** FastAPI / SQLAlchemy（后端），Vue 3 / Element Plus / TypeScript（前端），openpyxl（Excel 导出）

---

## 0. 文件结构

| 操作 | 文件 |
|------|------|
| 修改 | `backend/models/pi.py` |
| 修改 | `backend/crud/pi.py` |
| 修改 | `backend/routers/bff.py` |
| 修改 | `backend/routers/export.py` |
| 创建 | `backend/exporters/quote_exporter.py` |
| 修改 | `frontend/src/types/orderSummary.d.ts` |
| 修改 | `frontend/src/components/order/ProductEditDialog.vue` |
| 创建 | `frontend/src/components/order/NegotiationDialog.vue` |
| 修改 | `frontend/src/views/order/OrderDetailPanel.vue` |

---

## 任务 1：后端模型新增列

**文件：** `backend/models/pi.py`

- [ ] **步骤 1：确认类定义位置**

在 `models/pi.py` 中找到 `PiProformaInvoiceItem` 类定义，在 `invoice_status` 列（第93行附近）之后添加三列：

```python
    negotiation_history = Column(Text, nullable=True)  # JSON数组，存储多轮议价记录
    confirm_info = Column(Text, nullable=True)       # 确定信息
    quote_remark = Column(Text, nullable=True)         # 报价备注
```

- [ ] **步骤 2：验证语法**

```bash
python -c "import ast; ast.parse(open('models/pi.py', encoding='utf-8').read()); print('ok')"
```

预期：输出 `ok`，无报错

- [ ] **步骤 3：Commit**

```bash
git add backend/models/pi.py
git commit -m "feat(order): add negotiation_history, confirm_info, quote_remark columns to PiProformaInvoiceItem"
```

---

## 任务 2：后端 CRUD 层支持新字段读写

**文件：** `backend/crud/pi.py`

- [ ] **步骤 1：确认 import**

在文件顶部确认已有 `import json`，如果没有则添加：

```python
import json
```

- [ ] **步骤 2：找到 update_pi_item 中 `invoice_status` 处理位置**

在 `update_pi_item` 函数中，在 `if 'invoice_status' in update_data:` 块（第1268行附近）之后添加：

```python
    if 'negotiation_history' in update_data:
        db_item.negotiation_history = json.dumps(update_data['negotiation_history'])
        print(f"[DEBUG] update_pi_item: 更新 negotiation_history")
    if 'confirm_info' in update_data:
        db_item.confirm_info = update_data['confirm_info']
        print(f"[DEBUG] update_pi_item: 更新 confirm_info={update_data['confirm_info']}")
    if 'quote_remark' in update_data:
        db_item.quote_remark = update_data['quote_remark']
        print(f"[DEBUG] update_pi_item: 更新 quote_remark={update_data['quote_remark']}")
```

- [ ] **步骤 3：验证语法**

```bash
python -c "import ast; ast.parse(open('crud/pi.py', encoding='utf-8').read()); print('ok')"
```

预期：输出 `ok`

- [ ] **步骤 4：Commit**

```bash
git add backend/crud/pi.py
git commit -m "feat(order): handle negotiation_history, confirm_info, quote_remark in update_pi_item"
```

---

## 任务 3：BFF 层返回新字段

**文件：** `backend/routers/bff.py`

- [ ] **步骤 1：确认 import**

文件顶部已有 `from typing import Optional, Dict, Any, List`，确认有 `import json`，如果没有则添加：

```python
import json
```

- [ ] **步骤 2：修改 `_build_order_detail_item` 函数签名**

在第357行函数签名处，将：
```python
def _build_order_detail_item(
    item: PiProformaInvoiceItem,
    pi_no: str,
    order_date: Optional[str],
    latest_1688: Any = None,
    request: Optional[Request] = None,
) -> OrderDetailItemSchema:
```

改为在返回值中增加三个字段（位置在 `invoice_status` 之后）：

```python
        invoice_status=_to_str(item.invoice_status),
        negotiation_history=json.loads(item.negotiation_history) if item.negotiation_history else [],
        confirm_info=_to_str(item.confirm_info),
        quote_remark=_to_str(item.quote_remark),
    )
```

- [ ] **步骤 3：更新 `OrderDetailItemSchema` 定义**

找到 `schemas/bff_order.py`，在 `OrderDetailItemSchema` 中添加三个字段：

```python
    negotiation_history: List[Dict[str, Any]] = []
    confirm_info: str = ""
    quote_remark: str = ""
```

- [ ] **步骤 4：验证语法**

```bash
python -c "import ast; ast.parse(open('routers/bff.py', encoding='utf-8').read()); print('bff ok')"
python -c "import ast; ast.parse(open('schemas/bff_order.py', encoding='utf-8').read()); print('schema ok')"
```

- [ ] **步骤 5：Commit**

```bash
git add backend/routers/bff.py backend/schemas/bff_order.py
git commit -m "feat(bff): return negotiation_history, confirm_info, quote_remark in full-detail"
```

---

## 任务 4：前端类型定义

**文件：** `frontend/src/types/orderSummary.d.ts`

- [ ] **步骤 1：在 `OrderDetailItem` 接口末尾添加字段**

在 `invoice_status` 字段之后添加：

```typescript
  negotiation_history: Array<{
    demand: string
    reply: string
    demand_at: string
    reply_at: string | null
  }> | null
  confirm_info: string | null
  quote_remark: string | null
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/types/orderSummary.d.ts
git commit -m "feat(types): add negotiation_history, confirm_info, quote_remark to OrderDetailItem"
```

---

## 任务 5：ProductEditDialog 新增字段

**文件：** `frontend/src/components/order/ProductEditDialog.vue`

- [ ] **步骤 1：在 `ProductEditForm` 接口添加三个字段**

在 `invoice_status` 字段之后添加：

```typescript
  negotiation_history: Array<{
    demand: string
    reply: string
    demand_at: string
    reply_at: string | null
  }> | null
  confirm_info: string
  quote_remark: string
```

- [ ] **步骤 2：在 reactive form 默认值中添加三个字段默认值**

在 `invoice_status: ''` 之后添加：

```typescript
  negotiation_history: null,
  confirm_info: '',
  quote_remark: '',
```

- [ ] **步骤 3：在 `initFromItem` 函数中读取三个字段**

在 `form.invoice_status = source.invoice_status || ''` 之后添加：

```typescript
  form.confirm_info = (source as any).confirm_info || ''
  form.quote_remark = (source as any).quote_remark || ''
```

（`negotiation_history` 不需要从 item 读取，由 `NegotiationDialog` 独立管理）

- [ ] **步骤 4：在模板中添加 `confirm_info` 和 `quote_remark` 的 FieldInput**

在 `invoice_status` 相关行之后添加（位置参考 ProductEditDialog.vue 销售细节区末尾）：

```html
<div class="basic-info-label">确定信息<br />Confirmation</div>
<div class="basic-info-cell">
  <FieldInput
    v-model="form.confirm_info"
    :status="getFieldStatus('confirm_info')"
    @blur="saveField('confirm_info', form.confirm_info)"
  />
</div>
<div class="basic-info-label">报价备注<br />Q.Notes</div>
<div class="basic-info-cell">
  <FieldInput
    v-model="form.quote_remark"
    :status="getFieldStatus('quote_remark')"
    @blur="saveField('quote_remark', form.quote_remark)"
  />
</div>
```

- [ ] **步骤 5：验证构建**

```bash
npm run build
```

预期：`✓ built` 无 TypeScript 报错

- [ ] **步骤 6：Commit**

```bash
git add frontend/src/components/order/ProductEditDialog.vue
git commit -m "feat(order): add confirm_info and quote_remark fields to ProductEditDialog"
```

---

## 任务 6：新建 NegotiationDialog.vue

**文件：** `frontend/src/components/order/NegotiationDialog.vue`

- [ ] **步骤 1：创建 Dialog 组件**

创建文件 `frontend/src/components/order/NegotiationDialog.vue`，内容结构：

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="600px"
    :close-on-click-modal="true"
    destroy-on-close
  >
    <div class="negotiation-list">
      <div v-if="history.length === 0" class="empty-tip">暂无议价记录</div>
      <div v-for="(round, index) in history" :key="index" class="round-item">
        <div class="round-header">第 {{ history.length - index }} 轮</div>
        <div class="round-demand">
          <span class="label">客户需求：</span>
          <el-input
            v-model="round.demand"
            type="textarea"
            :rows="2"
            :disabled="!!round.reply_at"
            @blur="onDemandBlur(round)"
          />
          <span class="time">{{ round.demand_at ? formatTime(round.demand_at) : '' }}</span>
        </div>
        <div class="round-reply">
          <span class="label">我方答复：</span>
          <el-input
            v-model="round.reply"
            type="textarea"
            :rows="2"
            @blur="onReplyBlur(round)"
          />
          <span class="time">{{ round.reply_at ? formatTime(round.reply_at) : '' }}</span>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button type="primary" @click="onAddDemand">添加需求</el-button>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { orderSummaryApi } from '@/api/orderSummary'

const props = defineProps<{
  itemId: number
  productName: string
  initialHistory: Array<{
    demand: string
    reply: string
    demand_at: string
    reply_at: string | null
  }> | null
}>()

const emit = defineEmits<{
  (e: 'saved', history: any[]): void
}>()

const visible = ref(false)
const history = ref<any[]>([])

const dialogTitle = computed(() => `议价沟通记录 - ${props.productName || ''}`)

function open() {
  history.value = props.initialHistory ? [...props.initialHistory] : []
  visible.value = true
}

function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-CN')
}

async function saveHistory() {
  try {
    const res = await orderSummaryApi.updateOrderItem(props.itemId, {
      negotiation_history: history.value
    })
    if (res.data.success) {
      emit('saved', history.value)
    } else {
      ElMessage.error('保存失败')
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  }
}

function onDemandBlur(round: any) {
  if (!round.demand_at) {
    round.demand_at = new Date().toISOString()
  }
  saveHistory()
}

function onReplyBlur(round: any) {
  if (round.reply && !round.reply_at) {
    round.reply_at = new Date().toISOString()
  }
  saveHistory()
}

function onAddDemand() {
  history.value.push({
    demand: '',
    reply: '',
    demand_at: new Date().toISOString(),
    reply_at: null
  })
  saveHistory()
}

defineExpose({ open })
</script>

<style scoped>
.negotiation-list {
  max-height: 60vh;
  overflow-y: auto;
}
.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px;
}
.round-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 12px;
}
.round-header {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.round-demand, .round-reply {
  margin-bottom: 8px;
}
.label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}
.time {
  display: block;
  font-size: 11px;
  color: #c0c4cc;
  text-align: right;
  margin-top: 2px;
}
</style>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/order/NegotiationDialog.vue
git commit -m "feat(order): add NegotiationDialog for multi-round demand/reply history"
```

---

## 任务 7：OrderDetailPanel 双击打开 NegotiationDialog

**文件：** `frontend/src/views/order/OrderDetailPanel.vue`

- [ ] **步骤 1：导入 NegotiationDialog**

在文件顶部 import 区添加：

```typescript
import NegotiationDialog from '@/components/order/NegotiationDialog.vue'
```

- [ ] **步骤 2：注册 component**

在 `<script setup>` 的 `components` 中或通过顶层 `defineComponent` 注册 `NegotiationDialog`

- [ ] **步骤 3：在 `<template>` 中声明组件**

在 `<el-table>` 之前添加：

```vue
<NegotiationDialog
  ref="negotiationDialogRef"
  :item-id="editingItemId"
  :product-name="editingItemName"
  :initial-history="editingItemHistory"
  @saved="onNegotiationSaved"
/>
```

- [ ] **步骤 4：添加 ref 和状态变量**

在 `<script setup>` 中添加：

```typescript
const negotiationDialogRef = ref<InstanceType<typeof NegotiationDialog>>()
const editingItemId = ref(0)
const editingItemName = ref('')
const editingItemHistory = ref<any[] | null>(null)

function onNegotiationSaved(history: any[]) {
  // 触发父组件刷新详情
  // 可通过重新拉取 full-detail 或直接更新本地 store
}
```

- [ ] **步骤 5：找到 customer_demand 和 reply 列，给 el-table-column 加双击事件**

找到 `customer_demand` 列的 `<template #default="{ row }">` 块，给外层 `<div>` 加 `@dblclick`：

```html
<div @dblclick="openNegotiation(row)">
  <!-- 原有的 el-input 或文本显示保持不变 -->
</div>
```

同样给 `reply` 列加 `@dblclick="openNegotiation(row)"`。

- [ ] **步骤 6：添加 openNegotiation 方法**

```typescript
function openNegotiation(row: OrderDetailItem) {
  editingItemId.value = row.id
  editingItemName.value = row.product_name || ''
  editingItemHistory.value = row.negotiation_history || null
  negotiationDialogRef.value?.open()
}
```

- [ ] **步骤 7：验证构建**

```bash
npm run build
```

预期：`✓ built`

- [ ] **步骤 8：Commit**

```bash
git add frontend/src/views/order/OrderDetailPanel.vue
git commit -m "feat(order): double-click demand/reply columns to open NegotiationDialog"
```

---

## 任务 8：报价单导出器

**文件：** `backend/exporters/quote_exporter.py`（新建）

- [ ] **步骤 1：参考 PIExporter 创建 QuoteExporter**

参考 `exporters/pi_exporter.py`，新建 `exporters/quote_exporter.py`，核心差异：
- 类名：`QuoteExporter`
- 方法：`export_quotation(self, pi_data: Dict[str, Any], db) -> bytes`
- 在产品明细 sheet（Sheet1 或专门 sheet）新增"议价沟通记录"列或备注区，格式：

```
# 每行产品，议价记录列内容格式（多行用 \n 分隔）：
第1轮 [时间] 客户需求: xxx | 我方答复: xxx
第2轮 [时间] 客户需求: xxx | 我方答复: xxx
```

- [ ] **步骤 2：在 `exporters/__init__.py` 中导出 QuoteExporter**

在 `__init__.py` 中添加：

```python
from .quote_exporter import QuoteExporter
```

- [ ] **步骤 3：在 `routers/export.py` 中添加报价单路由**

在 `export_pi` 之后添加：

```python
@router.get("/quotation/{pi_id}")
def export_quotation(pi_id: int, db=None):
    """导出报价单（含议价沟通历史）"""
    try:
        if db is None:
            db = get_db_session()

        from crud.pi import get_pi_invoice_detail
        pi_data = get_pi_invoice_detail(db, pi_id)
        if not pi_data:
            raise HTTPException(status_code=404, detail="PI单不存在")

        exporter = QuoteExporter()
        excel_bytes = exporter.export_quotation(pi_data, db)

        filename = f"Quotation_{pi_data.get('pi_no', pi_id)}.xlsx"
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **步骤 4：验证语法**

```bash
python -c "import ast; ast.parse(open('exporters/quote_exporter.py', encoding='utf-8').read()); print('ok')"
```

- [ ] **步骤 5：Commit**

```bash
git add backend/exporters/quote_exporter.py backend/exporters/__init__.py backend/routers/export.py
git commit -m "feat(export): add QuoteExporter for quotation with negotiation history"
```

---

## 任务 9：前端报价单导出入口

**文件：** `frontend/src/components/order/PiOperationDialog.vue` 或现有操作入口

- [ ] **步骤 1：找到 PI 导出按钮位置**

在 `PiOperationDialog.vue` 或 `OrderDetailPanel.vue` 中找到"导出PI"按钮附近

- [ ] **步骤 2：添加"导出报价单"按钮**

在导出 PI 按钮之后添加：

```vue
<el-button @click="exportQuotation">导出报价单</el-button>
```

- [ ] **步骤 3：添加 exportQuotation 方法**

```typescript
async function exportQuotation() {
  if (!currentOrder.value?.id) return
  try {
    const res = await fetch(
      apiUrl(`/api/export/quotation/${currentOrder.value.id}`)
    )
    if (!res.ok) throw new Error()
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Quotation_${currentOrder.value.pi_no || currentOrder.value.id}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出报价单失败')
  }
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/views/order/OrderDetailPanel.vue  # 或 PiOperationDialog.vue
git commit -m "feat(order): add export quotation button"
```

---

## 自检清单

- [ ] 规格第2.1节 `negotiation_history` JSON 结构有对应任务（任务1+2+3）
- [ ] 规格第2.2节 `confirm_info`/`quote_remark` 列有对应任务（任务1+2+3）
- [ ] 规格第3.1节 BFF 返回新字段有对应任务（任务3）
- [ ] 规格第3.2节 `update_pi_item` 处理有对应任务（任务2）
- [ ] 规格第5.1节表格列显示有对应任务（任务7）
- [ ] 规格第5.2节 NegotiationDialog 有对应任务（任务6）
- [ ] 规格第6节报价单导出有对应任务（任务8+9）
- [ ] 所有任务中的文件路径、函数名、字段名相互一致
