# 订单管理总表 Web 化实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 PyQt 桌面端的「订单管理总表」完整迁移到 Vue 3 Web 端，包括 15 列订单列表视图和 41 列订单详情视图，功能与桌面端完全对齐。

**架构：** 采用「双视图切换」模式（与 PyQt 版一致）：列表视图展示订单级汇总信息，点击/双击进入详情视图展示产品级 41 列详细数据。后端通过 BFF 聚合接口提供数据，通过 QWebChannel 桥接 PyQt 原生能力（文件对话框、Excel 读写等）。

**技术栈：** Vue 3 + TypeScript + Pinia + Element Plus + Vite + FastAPI BFF + QWebChannel

---

## 文件结构

### 前端 (frontend/src/)
- `views/order/OrderSummary.vue` - 订单总表主容器（双视图切换，类似 OrderSummaryTab）
- `views/order/OrderListPanel.vue` - 订单列表面板（15 列，类似 OrderListPanel）
- `views/order/OrderDetailPanel.vue` - 订单详情面板（41 列，类似 OrderDetailPanel）
- `stores/orderSummaryStore.ts` - 订单总表状态管理（列表+详情+筛选+缓存）
- `api/orderSummary.ts` - 订单总表 API 封装（BFF 接口）
- `types/orderSummary.d.ts` - 订单总表类型定义（41 列字段、订单列表字段）
- `composables/useOrderList.ts` - 订单列表逻辑复用
- `composables/useOrderDetail.ts` - 订单详情逻辑复用
- `components/order/` - 子组件（状态灯、进度条、操作按钮组等）

### 后端 (backend/)
- `routers/bff.py` - 扩展 BFF 接口（订单列表/详情/付款/采购/库存聚合）
- `schemas/bff_order.py` - BFF 响应 Schema

---

## 任务 1：数据模型与类型定义

**文件：**
- 创建：`frontend/src/types/orderSummary.d.ts`
- 创建：`backend/schemas/bff_order.py`

- [ ] **步骤 1：定义前端 TypeScript 类型**

```typescript
// frontend/src/types/orderSummary.d.ts

// 订单列表项（模式一：15 列视图）
export interface OrderListItem {
  id: number                          // PI 主键（隐藏列）
  pi_no: string                       // ORDER NO.
  customer_id: number
  customer_name: string               // 客户
  order_date: string                  // 订单日期
  item_count: number                  // 产品数
  total_amount: number                // 总金额
  status: number                      // 状态码
  status_label: string                // 状态文本
  paid_amount: number                 // 已付款
  unpaid_amount: number               // 未付款
  payment_progress: number            // 付款进度 (0-100)
  payment_status: string              // 付款状态文本
  stock_remaining: number             // 库存剩余
}

// 订单详情项（模式二：41 列视图，每行一个产品）
export interface OrderDetailItem {
  // A组：基础信息 (0-8)
  order_date: string                  // Col 1
  pi_no: string                       // Col 2
  product_code: string                // Col 3 客户产品编号
  oe_number: string                   // Col 4 OE号
  remark: string                      // Col 5 客户需求/产品备注
  product_name: string                // Col 6 产品名称
  image_url: string                   // Col 7 图片
  customer_model: string              // Col 8 客户型号
  product_feature: string             // Col 9 产品特性

  // B组：价格财务 (9-20)
  quantity: number                    // Col 10 数量
  unit_price: number                  // Col 11 报价(USD/RMB)
  total_amount: number                // Col 12 合计金额
  latest_customer_reply: string       // Col 13 最新客户回复
  customer_prepayment: number         // Col 14 客户预付款
  remaining_payment: number           // Col 15 待收尾款
  estimated_usd_price: number         // Col 16 预估美金报价
  estimated_margin: number            // Col 17 预估毛利率
  purchase_price: number              // Col 18 采购价格
  shipping_fee: number                // Col 19 运费
  misc_fee: number                    // Col 20 杂费
  total_cost: number                  // Col 21 总金额(成本)

  // C组：供应商采购 (21-26)
  factory_name: string                // Col 22 工厂简称
  shop_url: string                    // Col 23 店铺链接
  delivery_date: string               // Col 24 交货日期
  is_received: boolean                // Col 25 是否已收货
  factory_deposit: number             // Col 26 工厂订金
  factory_balance: number             // Col 27 工厂尾款

  // D组：物流入库 (27-29)
  stock_in_action: string             // Col 28 入库操作
  stock_in_quantity: number           // Col 29 入库数量
  packaging: string                   // Col 30 包装方式

  // E组：产品细节 (30-38)
  purchase_option_name: string        // Col 31 采购选项/名称
  product_detail: string              // Col 32 产品细节
  factory_code: string                // Col 33 工厂编号
  carton_size: string                 // Col 34 纸箱尺寸
  pack_spec: string                   // Col 35 打包规格
  carton_count: number                // Col 36 箱数
  estimated_volume: number            // Col 37 预估体积
  carton_gross_weight: number         // Col 38 整箱毛重
  total_weight: number                // Col 39 总重量

  // F组：其他属性 (39-40)
  brand: string                       // Col 40 品牌
  invoice_status: string              // Col 41 开票情况
}

// 列表筛选参数
export interface OrderListFilter {
  search?: string
  status?: number
  customer_id?: number
  date_from?: string
  date_to?: string
}

// 分页参数
export interface OrderListParams extends OrderListFilter {
  page: number
  page_size: number
}

// BFF 响应
export interface OrderListResponse {
  list: OrderListItem[]
  total: number
  page: number
  page_size: number
}

export interface OrderDetailResponse {
  order: OrderListItem
  items: OrderDetailItem[]
}
```

- [ ] **步骤 2：定义后端 Pydantic Schema**

```python
# backend/schemas/bff_order.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class OrderListItemSchema(BaseModel):
    id: int
    pi_no: str
    customer_id: int
    customer_name: str
    order_date: Optional[str] = None
    item_count: int = 0
    total_amount: float = 0
    status: int = 1
    status_label: str = ""
    paid_amount: float = 0
    unpaid_amount: float = 0
    payment_progress: float = 0
    payment_status: str = "未付款"
    stock_remaining: float = 0

class OrderDetailItemSchema(BaseModel):
    id: int
    order_date: Optional[str] = None
    pi_no: str = ""
    product_code: str = ""
    oe_number: str = ""
    remark: str = ""
    product_name: str = ""
    image_url: str = ""
    customer_model: str = ""
    product_feature: str = ""
    quantity: float = 0
    unit_price: float = 0
    total_amount: float = 0
    latest_customer_reply: str = ""
    customer_prepayment: float = 0
    remaining_payment: float = 0
    estimated_usd_price: float = 0
    estimated_margin: float = 0
    purchase_price: float = 0
    shipping_fee: float = 0
    misc_fee: float = 0
    total_cost: float = 0
    factory_name: str = ""
    shop_url: str = ""
    delivery_date: Optional[str] = None
    is_received: bool = False
    factory_deposit: float = 0
    factory_balance: float = 0
    stock_in_action: str = ""
    stock_in_quantity: float = 0
    packaging: str = ""
    purchase_option_name: str = ""
    product_detail: str = ""
    factory_code: str = ""
    carton_size: str = ""
    pack_spec: str = ""
    carton_count: int = 0
    estimated_volume: float = 0
    carton_gross_weight: float = 0
    total_weight: float = 0
    brand: str = ""
    invoice_status: str = ""

class OrderListResponseSchema(BaseModel):
    list: List[OrderListItemSchema]
    total: int
    page: int
    page_size: int

class OrderDetailResponseSchema(BaseModel):
    order: OrderListItemSchema
    items: List[OrderDetailItemSchema]
```

- [ ] **步骤 3：验证类型定义**

运行：`cd frontend && npx vue-tsc --noEmit`
预期：类型检查通过

---

## 任务 2：BFF 后端接口完善

**文件：**
- 修改：`backend/routers/bff.py`
- 修改：`backend/main.py`（注册已完成，无需改动）

- [ ] **步骤 1：完善订单列表 BFF 接口**

在 `backend/routers/bff.py` 中扩展 `/orders` 接口，补充付款状态、库存剩余等聚合字段，完全对齐 15 列列表。

关键聚合逻辑：
- 已付款/未付款：关联 `pi_payment_stage` 表计算
- 付款进度：已付款 / 总金额 * 100
- 库存剩余：关联库存表计算
- 产品数：统计 `pi_proforma_invoice_item` 非删除项

- [ ] **步骤 2：实现订单详情 BFF 接口（41列）**

新增 `/orders/{order_id}/full-detail` 接口，返回完整 41 列产品数据。

数据来源映射：
- A组基础信息 → `pi_proforma_invoice` + `pi_proforma_invoice_item` + `prd_customer_product`
- B组价格财务 → `pi_proforma_invoice_item` + 付款表
- C组供应商采购 → `po_purchase_order_item`（回写字段）
- D组物流入库 → `pi_proforma_invoice_item`（入库回写字段）
- E组产品细节 → `pi_proforma_invoice_item`（细节/包装字段）
- F组其他属性 → `pi_proforma_invoice_item`（品牌/开票）

- [ ] **步骤 3：实现订单仪表盘 BFF 接口**

完善 `/orders/dashboard` 接口，返回：
- 订单总数
- 总金额
- 各状态订单数
- 付款统计

- [ ] **步骤 4：验证后端接口**

运行：`cd backend && python -c "from routers.bff import router; print('BFF import OK')"`
预期：无错误

手动测试：启动后端后访问 `http://localhost:8000/api/bff/orders?page=1&page_size=20`
预期：返回 JSON 格式正确

---

## 任务 3：Pinia Store 重构

**文件：**
- 重命名：`frontend/src/stores/orderStore.ts` → `frontend/src/stores/orderSummaryStore.ts`
- 扩展：状态结构对齐 OrderListPanel + OrderDetailPanel

- [ ] **步骤 1：重写 orderSummaryStore**

```typescript
// 核心 state
const viewMode = ref<'list' | 'detail'>('list')      // 视图模式
const orders = ref<OrderListItem[]>([])               // 订单列表
const currentOrder = ref<OrderListItem | null>(null)  // 当前选中订单
const detailItems = ref<OrderDetailItem[]>([])        // 当前订单详情项
const selectedIds = ref<Set<number>>(new Set())       // 选中的订单ID
const filter = ref<OrderListFilter>({})               // 筛选条件
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

// 核心 actions
fetchOrders(params?)               // 加载订单列表
fetchOrderDetail(orderId)          // 加载订单详情（41列）
setViewMode(mode)                  // 切换列表/详情视图
toggleSelect(id)                   // 切换选中
clearSelection()                   // 清空选中
setFilter(newFilter)               // 更新筛选
```

- [ ] **步骤 2：验证 Store 类型**

运行：`cd frontend && npx vue-tsc --noEmit`
预期：无类型错误

---

## 任务 4：订单列表视图组件（15 列）

**文件：**
- 创建：`frontend/src/views/order/OrderListPanel.vue`

功能完全对齐 `order_list_panel.py` 的 15 列：
1. 选择（复选框）
2. ORDER NO.
3. 客户
4. 订单日期
5. 产品数
6. 总金额
7. 状态
8. 已付款
9. 未付款
10. 付款进度（进度条）
11. 库存剩余
12. 添加付款（按钮）
13. PI操作（多形态按钮）
14. 编辑
15. [隐藏] PI 主键

- [ ] **步骤 1：实现列表表格主体**

使用 Element Plus `el-table`，列定义完全对齐 15 列。
- 第 0 列：复选框（`type="selection"`）
- 金额列：右对齐 + 千分位格式
- 付款进度列：`el-progress` 进度条
- 状态列：`el-tag` 标签
- 操作列：按钮组

- [ ] **步骤 2：实现顶部工具栏**

- 搜索框（订单号/客户名）
- 状态筛选下拉
- 日期范围筛选
- 新增订单按钮
- 刷新按钮
- 批量删除按钮

- [ ] **步骤 3：实现行点击事件**

- 单击：选中行（高亮）
- 双击：进入详情视图
- 复选框：多选模式

- [ ] **步骤 4：验证列表组件**

启动前端开发服务器，访问订单列表页
预期：表格正确渲染 15 列，分页正常，搜索可用

---

## 任务 5：订单详情视图组件（41 列）

**文件：**
- 创建：`frontend/src/views/order/OrderDetailPanel.vue`

功能完全对齐 `order_detail_panel.py` 的 41 列，分 6 组：
- A组：基础信息（列 0-8）
- B组：价格财务（列 9-20）
- C组：供应商采购（列 21-26）
- D组：物流入库（列 27-29）
- E组：产品细节（列 30-38）
- F组：其他属性（列 39-40）

- [ ] **步骤 1：实现 41 列表格**

使用 `el-table` 实现 41 列，分组显示（可折叠列组）。
- 图片列：缩略图显示
- 数值列：右对齐
- 长文本列：鼠标悬停 tooltip
- 固定列：前 3 列固定左侧

- [ ] **步骤 2：实现顶部操作栏**

- 返回按钮（回到列表视图）
- 订单信息标题（订单号 + 客户名）
- 采购全部按钮
- 补充商品按钮
- 出货按钮
- 导出 Excel 按钮
- 导入 Excel 按钮
- 添加付款按钮

- [ ] **步骤 3：实现右键菜单**

对齐 PyQt 版右键菜单：
- 采购该产品
- 重新采购
- 入库该产品
- 删除商品
- 编辑产品
- 更换供应商
- 访问店铺网站

- [ ] **步骤 4：实现行内编辑**

双击单元格可编辑（数量、单价等），编辑后自动保存。

- [ ] **步骤 5：验证详情组件**

启动前端，从列表点击进入详情
预期：41 列正确显示，右键菜单可用，操作按钮正常

---

## 任务 6：主容器组件（双视图切换）

**文件：**
- 创建：`frontend/src/views/order/OrderSummary.vue`
- 修改：`frontend/src/router/index.ts`

功能对齐 `order_summary_tab.py`：
- 两页式切换布局（列表 ↔ 详情）
- 视图状态管理
- 信号转发（通过 Pinia store 实现）

- [ ] **步骤 1：实现双视图切换容器**

- 默认显示列表视图
- 双击列表行切换到详情视图
- 详情视图点击返回按钮回到列表
- 使用 transition 动画

- [ ] **步骤 2：集成 QWebChannel 桥接**

- Excel 导入：调用 PyQt 文件对话框 + Excel 读取
- Excel 导出：调用 PyQt 文件保存对话框 + Excel 写入
- 系统通知：调用 PyQt 原生通知

- [ ] **步骤 3：更新路由**

将 `/orders` 路由指向 `OrderSummary.vue`

- [ ] **步骤 4：验证主容器**

访问 `/orders`，测试列表→详情→返回流程
预期：切换流畅，状态保持正确

---

## 任务 7：Excel 导入导出集成

**文件：**
- 修改：`frontend/src/views/order/OrderDetailPanel.vue`
- 修改：`backend/routers/bff.py`

- [ ] **步骤 1：实现 Excel 导入**

流程：
1. 点击"导入产品"按钮
2. 通过 QWebChannel 调用 PyQt 文件对话框
3. 选择 Excel 文件
4. 通过 QWebChannel 调用 PyQt 读取 Excel
5. 预览数据（前 20 行）
6. 确认后调用后端 BFF 接口批量导入

- [ ] **步骤 2：实现 Excel 导出**

流程：
1. 点击"导出"按钮
2. 通过 QWebChannel 调用 PyQt 保存文件对话框
3. 选择保存路径
4. 调用后端接口获取完整数据
5. 通过 QWebChannel 调用 PyQt 写入 Excel

- [ ] **步骤 3：验证导入导出**

手动测试：从 PyQt 客户端打开 Web 订单，测试导入导出
预期：文件对话框正常弹出，Excel 读写正确

---

## 任务 8：集成测试与冒烟验证

- [ ] **步骤 1：完整流程测试**

测试完整用户流程：
1. 打开 Web 订单页面 → 显示订单列表
2. 使用搜索/筛选 → 列表正确过滤
3. 双击某订单 → 进入详情视图，显示 41 列
4. 右键产品 → 菜单正确显示
5. 点击返回 → 回到列表视图
6. 导入 Excel → 文件对话框弹出，预览正常
7. 导出 Excel → 文件保存成功

- [ ] **步骤 2：性能测试**

- 1000 条订单列表加载时间 < 2s
- 500 行详情表格滚动流畅

- [ ] **步骤 3：兼容性测试**

- PyQt 客户端内嵌入显示正常
- 浏览器直接访问也正常
- QWebChannel 通信稳定

---

## 注意事项

1. **字段映射**：严格对齐 `constants.py` 中的 41 列定义，列顺序和命名与 PyQt 版完全一致
2. **状态映射**：数字状态码（0-3）→ 中文文本，使用统一的 STATUS_MAP
3. **数据聚合**：BFF 层负责聚合多表数据，前端不做复杂计算
4. **渐进式加载**：列表只加载订单级数据，详情进入后才加载 41 列产品数据
5. **QWebChannel 降级**：当不在 PyQt 环境中运行时（直接浏览器访问），提供降级方案（使用 HTML5 文件 API）
6. **类型安全**：所有 41 列字段都有完整 TypeScript 类型定义
