# 出货管理模块 — 第一轮设计

> 状态：已完成实现

## 1. 目标与范围

将旧 PyQt 出货 Tab（`client/widgets/shipment_tab.py`）的核心功能迁移到 Web 前端，分多轮实现。

**本轮（Round 1）范围：**
- 出货单列表（只读）+ 独立路由 `/shipments`
- 从订单列表创建出货单（跨 PI 选产品 + 调用 `POST /api/shipments/from-orders`）
- 订单列表页入口：`创建出货单` 按钮 + `出货管理` 按钮

**下一轮（Round 2+）：**
- 出货单详情页 `/shipments/:id`（19 列出货明细表格）
- 出货阶段（Stage）管理
- CI / PL 文档编辑与导出

## 2. 后端接口（已存在，无需新增）

| 接口 | 方法 | 用途 |
|------|------|------|
| `/api/shipments` | GET | 出货单列表 |
| `/api/shipments/{id}` | GET | 出货单详情（Round 2） |
| `/api/shipments/shippable-items` | GET | 获取 PI 内可出货产品 |
| `/api/shipments/from-orders` | POST | 从订单创建出货单 |
| `/api/shipments/{id}/confirm` | POST | 确认出货单 |

**关键说明：**
- `GET /api/shipments` 直接返回 `Shipment[]`，非 `{code, data}` 包装。
- `POST /api/shipments/from-orders` 支持多 PI 合并（`pi_ids` 数组）。
- `shippable-items` 自动计算 `remaining_quantity = order_quantity - shipped_quantity`。
- 列表接口暂无分页参数，前端以全部数据加载。

## 3. 文件结构

```
frontend/src/
  types/shipment/
    index.ts          # barrel
    shipment.d.ts     # 所有类型定义
  api/
    shipments.ts      # API 客户端
  stores/
    shipmentStore.ts   # Pinia store
  components/shipment/
    ShipmentProductPicker.vue  # PI多选 + 产品勾选子组件
    ShipmentCreateDialog.vue   # 创建出货单对话框
    ShipmentListPanel.vue      # 列表 + 筛选 + 分页
  views/shipment/
    ShipmentsPage.vue          # 顶层页面容器
  router/index.ts              # 新增 /shipments 路由
  views/order/
    OrderListPanel.vue         # 新增"创建出货单"+"出货管理"按钮
```

## 4. 数据流

### 列表加载

1. `ShipmentsPage` 挂载 → `store.fetchList()`
2. Store 调用 `GET /api/shipments` → 写入 `list.value`
3. `ShipmentListPanel` 渲染表格（11 列，复刻 PyQt）
4. 状态/关键词变化 → 防抖 300ms → 重新 fetch（前端过滤，暂无后端分页）

### 创建出货单

1. 订单列表点击"创建出货单" → `ShipmentCreateDialog.open()`
2. `ShipmentProductPicker` 加载已确认 PI（`status=2`）多选列表
3. 选中 PI 后 → 调用 `GET /api/shipments/shippable-items?pi_ids=...`
4. 渲染可出货明细，用户输入本次出货数量和单价
5. 点击"创建" → `POST /api/shipments/from-orders`
6. 成功后关闭对话框，刷新列表，提示"出货单创建成功"

## 5. UI 样式

- **列表 Toolbar**：与 `OrderListPanel` 风格一致，筛选器 + 搜索框 + 刷新按钮
- **状态颜色**：与 PyQt `STATUS_COLOR` 完全一致（橙/蓝/绿/灰）
- **分页**：底部 `el-pagination`，默认每页 20 条
- **创建对话框**：宽度 900px，左侧 PI 多选 + 右侧产品明细表格

## 6. 类型定义

- `ShipmentStatus`：枚举 1-4，对应 4 种状态
- `Shipment`：列表行，匹配后端 `serialize_shipment()`
- `ShippableItem`：可出货明细，匹配后端 `get_shippable_items()`
- `ShipmentCreatePayload`：POST 请求体

## 7. 验证

- 前端：`npm run build` → exit 0
- 后端：`py -m py_compile routers/shipment.py` → exit 0

## 8. 已知限制（Round 2+ 解决）

- 列表暂无后端分页，全量加载
- 创建对话框中 cartons/volume/weight 由后端根据 `pack_spec` 自动计算，前端未展示预览
- 出货单详情页未实现（路由 `/shipments/:id` 暂为占位）
- 剩余箱数 / 体积自动计算未在对话框内实时预览
