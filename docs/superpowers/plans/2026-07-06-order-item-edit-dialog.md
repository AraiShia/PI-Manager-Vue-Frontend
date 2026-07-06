# 订单产品编辑 Dialog 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为订单详情页实现一个单个 PI item 的编辑 Dialog，支持按业务区块即时保存字段修改，并支持本地上传产品图片。

**架构：** 前端新增 `ProductEditDialog.vue` 组件，通过 `PATCH /api/pi/items/{item_id}` 即时保存字段；图片上传通过 PyQt 桥接本地文件选择 + 后端上传接口（浏览器环境回退到 file input）。`OrderDetailPanel.vue` 的双击和右键菜单接入该 Dialog。

**技术栈：** Vue 3 + TypeScript + Element Plus + Pinia + Axios；后端 FastAPI + SQLAlchemy。

---

## 文件结构

| 文件 | 类型 | 职责 |
|------|------|------|
| `frontend/src/components/order/ProductEditDialog.vue` | 创建 | 产品编辑 Dialog 主组件 |
| `frontend/src/composables/useProductEdit.ts` | 创建 | 字段保存状态、计算字段、校验逻辑的可复用组合式函数 |
| `frontend/src/api/orderSummary.ts` | 修改 | 添加 `updateOrderItem`、`uploadProductImage` API |
| `frontend/src/api/nativeBridge.ts` | 修改 | 添加 `uploadImage` / `readFileBuffer` 桥接方法 |
| `frontend/src/types/native.ts` | 修改 | 扩展 `NativeBridge` 类型定义 |
| `frontend/src/views/order/OrderDetailPanel.vue` | 修改 | 双击行与右键菜单接入 ProductEditDialog |
| `backend/routers/pi.py` | 修改 | 已有 `PUT /items/{item_id}`，补充图片上传路由 |
| `backend/crud/pi.py` | 修改 | 扩展 `update_pi_item` 支持的字段，新增图片保存 |
| `backend/models/pi.py` | 修改 | 为 `PiProformaInvoiceItem` 增加 `image_url` 字段 |
| `backend/app/main.py` 或静态目录 | 修改 | 配置上传文件静态服务 |

---

## 任务 1：后端数据库与模型 — 增加 image_url 字段

**文件：**
- 修改：`backend/models/pi.py:27-99`

- [ ] **步骤 1：在 PiProformaInvoiceItem 增加 image_url 字段**

```python
# 在 backend/models/pi.py 的 PiProformaInvoiceItem 类中新增
image_url = Column(String(500), nullable=True)  # 产品图片 URL
```

- [ ] **步骤 2：创建 Alembic 迁移脚本（如果项目使用 Alembic）**

运行：
```bash
cd backend
alembic revision -m "add image_url to pi_proforma_invoice_item"
```

在生成的迁移文件中添加：
```python
op.add_column('pi_proforma_invoice_item', sa.Column('image_url', sa.String(500), nullable=True))
```

- [ ] **步骤 3：应用迁移**

```bash
alembic upgrade head
```

- [ ] **步骤 4：Commit**

```bash
git add backend/models/pi.py backend/alembic/versions/xxx_add_image_url_to_pi_proforma_invoice_item.py
git commit -m "chore: add image_url column to pi_proforma_invoice_item"
```

---

## 任务 2：后端 API — 扩展 update_pi_item 字段与新增图片上传

**文件：**
- 修改：`backend/crud/pi.py:1059-1170`
- 修改：`backend/routers/pi.py:589-629`
- 创建：`backend/routers/upload.py`（如果项目没有统一上传路由）

- [ ] **步骤 1：扩展 update_pi_item 支持的设计文档字段**

在 `backend/crud/pi.py` 的 `update_pi_item` 中，补充以下字段映射：

```python
# 基础信息
if 'image_url' in update_data:
    db_item.image_url = update_data['image_url']
if 'factory_name' in update_data:
    db_item.supplier_name = update_data['factory_name']
if 'shop_url' in update_data:
    db_item.shop_url = update_data['shop_url']
if 'brand' in update_data:
    db_item.brand = update_data['brand']
if 'purchase_price' in update_data:
    db_item.purchase_price = update_data['purchase_price']
if 'shipping_fee' in update_data:
    db_item.shipping_fee = update_data['shipping_fee']
if 'misc_fee' in update_data:
    db_item.misc_fee = update_data['misc_fee']
if 'delivery_date' in update_data:
    db_item.delivery_date = update_data['delivery_date']
if 'stocked_qty' in update_data:
    db_item.stocked_qty = update_data['stocked_qty']

# 金额/价格重算
if 'quantity' in update_data or 'unit_price' in update_data:
    qty = float(db_item.quantity or 0)
    price = float(db_item.unit_price or 0)
    db_item.total_price = qty * price
    # 同步刷新 PI 主单 total_amount
    pi = db_item.pi
    if pi:
        pi.total_amount = db.query(func.sum(PiProformaInvoiceItem.total_price)).filter(
            PiProformaInvoiceItem.pi_id == pi.id,
            PiProformaInvoiceItem.is_deleted == False
        ).scalar() or 0
```

- [ ] **步骤 2：新增图片上传路由**

创建或修改上传路由文件 `backend/routers/upload.py`：

```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "product_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/product-image")
async def upload_product_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1] or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    return {
        "code": 200,
        "data": { "url": f"/uploads/product_images/{filename}" },
        "message": "上传成功"
    }
```

- [ ] **步骤 3：在 main.py 注册上传路由并挂载静态目录**

```python
from fastapi.staticfiles import StaticFiles
from routers import upload

app.include_router(upload.router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

- [ ] **步骤 4：运行后端 smoke test**

```bash
cd backend
python -m pytest tests/routers/test_pi.py -v -k "update_pi_item"  # 如果存在
# 或手动调用
```

- [ ] **步骤 5：Commit**

```bash
git add backend/crud/pi.py backend/routers/upload.py backend/main.py backend/models/pi.py
git commit -m "feat(backend): extend update_pi_item fields and add product image upload"
```

---

## 任务 3：前端 NativeBridge — 扩展图片上传能力

**文件：**
- 修改：`frontend/src/types/native.ts`
- 修改：`frontend/src/api/nativeBridge.ts`

- [ ] **步骤 1：扩展 NativeBridge 类型**

```typescript
// frontend/src/types/native.ts
export interface NativeBridge {
  selectFile: (filter: string) => Promise<string>
  saveFile: (defaultName: string) => Promise<string>
  readExcel: (path: string) => Promise<any[]>
  writeExcel: (path: string, data: any[]) => Promise<boolean>
  showNotification: (message: string) => void
  getAppVersion: () => Promise<string>
  getAppVersionName: () => Promise<string>
  versionAvailable?: { connect: (cb: (version: string) => void) => void }
  fileSelected?: { connect: (cb: (path: string) => void) => void }
  // 新增
  readFileAsBase64?: (path: string) => Promise<string>
  uploadImage?: (localPath: string, uploadUrl: string) => Promise<{ url: string }>
}
```

- [ ] **步骤 2：在 nativeBridge 对象中新增方法**

```typescript
// frontend/src/api/nativeBridge.ts
async readFileAsBase64(path: string): Promise<string> {
  return getBridge().readFileAsBase64!(path)
},

async uploadImage(localPath: string, uploadUrl: string): Promise<{ url: string }> {
  const b = getBridge()
  if (b.uploadImage) {
    return b.uploadImage(localPath, uploadUrl)
  }
  // fallback: JS 读取 base64 后自己上传
  const base64 = await b.readFileAsBase64!(localPath)
  const res = await fetch(uploadUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: Uint8Array.from(atob(base64), c => c.charCodeAt(0))
  })
  return await res.json()
}
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/types/native.ts frontend/src/api/nativeBridge.ts
git commit -m "feat(bridge): extend native bridge for image upload"
```

---

## 任务 4：前端 API 层 — 添加 item 更新与图片上传

**文件：**
- 修改：`frontend/src/api/orderSummary.ts`

- [ ] **步骤 1：添加 updateOrderItem 与 uploadProductImage**

```typescript
import client from './client'
import type { ApiResponse } from '@/types/api'

export interface OrderItemUpdatePayload {
  [key: string]: any
}

export const orderSummaryApi = {
  // ... 已有方法

  updateOrderItem: (itemId: number, payload: OrderItemUpdatePayload) =>
    client.put<ApiResponse<{ id: number; success: boolean }>>(
      `/api/pi/items/${itemId}`,
      payload
    ),

  uploadProductImage: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post<ApiResponse<{ url: string }>>(
      '/api/upload/product-image',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  }
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/api/orderSummary.ts
git commit -m "feat(api): add updateOrderItem and uploadProductImage APIs"
```

---

## 任务 5：前端可复用逻辑 — useProductEdit 组合式函数

**文件：**
- 创建：`frontend/src/composables/useProductEdit.ts`

- [ ] **步骤 1：编写 useProductEdit**

```typescript
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { orderSummaryApi } from '@/api/orderSummary'
import type { OrderDetailItem } from '@/types/orderSummary'

export type FieldStatus = 'idle' | 'saving' | 'success' | 'error'

export interface FieldState {
  status: FieldStatus
  message: string
}

export function useProductEdit(item: OrderDetailItem) {
  const fieldStates = ref<Record<string, FieldState>>({})
  const dirtyFields = ref<Set<string>>(new Set())

  function setFieldStatus(field: string, status: FieldStatus, message = '') {
    fieldStates.value[field] = { status, message }
  }

  async function saveField(field: string, value: any) {
    if (value === item[field as keyof OrderDetailItem]) return

    setFieldStatus(field, 'saving')
    dirtyFields.value.add(field)

    try {
      const res = await orderSummaryApi.updateOrderItem(item.id, { [field]: value })
      if (res.data.code === 200) {
        setFieldStatus(field, 'success', '已保存')
        ;(item as any)[field] = value
        dirtyFields.value.delete(field)
      } else {
        setFieldStatus(field, 'error', res.data.message || '保存失败')
      }
    } catch (e: any) {
      setFieldStatus(field, 'error', e.message || '保存失败')
      ElMessage.error(`${field} 保存失败`)
    }
  }

  const computedTotalAmount = computed(() => {
    const qty = Number(item.quantity || 0)
    const price = Number(item.unit_price || 0)
    return qty * price
  })

  return {
    fieldStates,
    dirtyFields,
    saveField,
    setFieldStatus,
    computedTotalAmount,
  }
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/composables/useProductEdit.ts
git commit -m "feat(composable): add useProductEdit for instant field save"
```

---

## 任务 6：前端主组件 — ProductEditDialog.vue

**文件：**
- 创建：`frontend/src/components/order/ProductEditDialog.vue`

- [ ] **步骤 1：创建基础 Dialog 模板**

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="`编辑产品 - ${item?.customer_model || item?.product_code || ''}`"
    width="90vw"
    top="5vh"
    :close-on-click-modal="false"
    destroy-on-close
    @close="onClose"
  >
    <div v-loading="loading" class="product-edit-dialog">
      <!-- 基础信息 -->
      <div class="edit-section" style="--section-color: #fde2e2;">
        <div class="section-title" style="background: #fde2e2; color: #c45650;">基础信息</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="form-item wide">
              <label class="required">客户</label>
              <el-input v-model="form.customer_name" disabled />
            </div>
            <div class="form-item">
              <label class="required">客户型号</label>
              <field-input
                v-model="form.customer_model"
                :status="fieldStates.customer_model?.status"
                @blur="saveField('customer_model', form.customer_model)"
              />
            </div>
            <div class="form-item all">
              <label class="required">产品名称</label>
              <field-input
                v-model="form.product_name"
                :status="fieldStates.product_name?.status"
                @blur="saveField('product_name', form.product_name)"
              />
            </div>
            <!-- 其他字段省略，按设计文档补全 -->
          </div>
        </div>
      </div>

      <!-- 销售细节、采购信息、入库信息、资料存档区块同理 -->
    </div>

    <template #footer>
      <el-button @click="onClose">关闭</el-button>
    </template>
  </el-dialog>
</template>
```

- [ ] **步骤 2：创建 FieldInput 子组件用于状态反馈**

创建 `frontend/src/components/order/FieldInput.vue`：

```vue
<template>
  <div class="field-input-wrapper">
    <el-input
      v-model="modelValue"
      :class="{ 'is-error': status === 'error', 'is-success': status === 'success' }"
      v-bind="$attrs"
      @blur="$emit('blur')"
    />
    <el-icon v-if="status === 'saving'" class="field-status-icon"><Loading /></el-icon>
    <el-icon v-else-if="status === 'success'" class="field-status-icon success"><Check /></el-icon>
    <el-icon v-else-if="status === 'error'" class="field-status-icon error"><CircleClose /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { Loading, Check, CircleClose } from '@element-plus/icons-vue'

defineProps<{ status?: string }>()
defineEmits(['blur', 'update:modelValue'])
</script>
```

- [ ] **步骤 3：实现图片上传逻辑**

```typescript
async function handleImageUpload(file: File) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file)
    if (res.data.code === 200) {
      form.image_url = res.data.data.url
      await saveField('image_url', form.image_url)
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/components/order/ProductEditDialog.vue frontend/src/components/order/FieldInput.vue
git commit -m "feat(dialog): add ProductEditDialog with instant save and image upload"
```

---

## 任务 7：前端集成 — OrderDetailPanel 接入 Dialog

**文件：**
- 修改：`frontend/src/views/order/OrderDetailPanel.vue:378-388`（右键菜单）
- 修改：`frontend/src/views/order/OrderDetailPanel.vue:762-837`（右键处理与双击）

- [ ] **步骤 1：调整右键菜单项**

```typescript
const contextMenuItems: ContextMenuItem[] = [
  { label: '编辑产品信息', action: 'edit', icon: Edit },
  { label: '复制', action: 'copy', icon: DocumentCopy },
  { label: '', action: 'divider1', divider: true },
  { label: '采购', action: 'purchase', icon: ShoppingCart },
  { label: '入库', action: 'stockIn', icon: Box },
  { label: '', action: 'divider2', divider: true },
  { label: '删除商品', action: 'delete', icon: Delete, danger: true },
]
```

- [ ] **步骤 2：注册 ProductEditDialog 并处理 edit/copy 动作**

```vue
<template>
  <!-- ... -->
  <ProductEditDialog ref="productEditDialogRef" @closed="onDetailSuccess" />
</template>

<script setup>
import ProductEditDialog from '@/components/order/ProductEditDialog.vue'
import { DocumentCopy } from '@element-plus/icons-vue'

const productEditDialogRef = ref<InstanceType<typeof ProductEditDialog>>()

function onCellDblClick(row: OrderDetailItem) {
  productEditDialogRef.value?.open(row)
}

async function handleContextMenuAction(action: string) {
  hideContextMenu()
  if (!currentContextRow.value) return
  const item = currentContextRow.value

  switch (action) {
    case 'edit':
      productEditDialogRef.value?.open(item)
      break
    case 'copy':
      // 复制产品逻辑（调用后端或本地复制）
      ElMessage.info('复制功能开发中')
      break
    case 'purchase':
      // 打开采购 Dialog
      break
    case 'stockIn':
      // 打开入库 Dialog
      break
    case 'delete':
      await deleteItem(item)
      break
  }
}
</script>
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/views/order/OrderDetailPanel.vue
git commit -m "feat(order-detail): wire ProductEditDialog to row dblclick and context menu"
```

---

## 任务 8：PyQt 壳桥接 — 实现 readFileAsBase64 / uploadImage

**文件：**
- 修改：`client/main.py` 或 `client/web_container/bridge.py`（取决于桥接实现位置）

- [ ] **步骤 1：在 PyQt Bridge 类中添加方法**

```python
import base64

class NativeBridge(QObject):
    # ... 已有方法

    @pyqtSlot(str, result=str)
    def readFileAsBase64(self, path: str) -> str:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @pyqtSlot(str, str, result=dict)
    def uploadImage(self, local_path: str, upload_url: str) -> dict:
        import requests
        with open(local_path, 'rb') as f:
            res = requests.post(upload_url, files={'file': f})
        return res.json()
```

- [ ] **步骤 2：Commit**

```bash
git add client/main.py  # 或 client/web_container/bridge.py
git commit -m "feat(pyqt-bridge): add image upload helpers for product edit dialog"
```

---

## 任务 9：集成测试

**文件：**
- 修改：`frontend/src/views/order/OrderDetailPanel.vue`

- [ ] **步骤 1：启动前后端**

```bash
.\start.ps1 -DevOnly
```

- [ ] **步骤 2：验证功能清单**

- 双击订单详情行打开 ProductEditDialog
- 修改客户型号，失焦后显示绿色 ✓
- 修改数量/报价，金额自动重算
- 上传图片后图片预览更新
- 关闭 Dialog 后订单详情刷新
- 右键菜单显示：编辑产品信息、复制、采购、入库、删除商品

- [ ] **步骤 3：Commit 最终版本**

```bash
git add .
git commit -m "feat(order): implement product edit dialog with instant save"
```

---

## 自检

- **规格覆盖度：** 所有设计文档需求都有对应任务（Dialog 规格、即时存储、5 个区块、图片上传、右键菜单）。
- **占位符扫描：** 无 TODO/待定。
- **类型一致性：** `OrderDetailItem` 字段名与 `update_pi_item` 参数、`form` 对象保持一致。
- **范围检查：** 本计划聚焦单个 Dialog，采购/入库独立 Dialog 后续单独实现。
