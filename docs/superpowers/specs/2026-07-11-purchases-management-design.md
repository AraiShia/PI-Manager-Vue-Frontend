# 采购订单管理页面设计

## 1. 目标与范围

将 `/purchases` 从占位页替换为可用的采购订单管理列表页，参考旧 PyQt 采购管理 Tab 行为。

**本轮实现**
- 采购订单列表加载、分页、搜索、状态筛选。
- 行操作：确认、入库、查看发票、导出合同。
- 工具栏：刷新。

**本轮不做**
- 新建/编辑采购单（创建走订单汇总页采购 Dialog）。
- 采购详情页。
- 1688/微信采购入口。

## 2. 架构与文件边界

### 新增文件

- `frontend/src/views/purchase/PurchaseManagement.vue`：采购管理页面入口。
- `frontend/src/api/purchase.ts`：扩展现有文件，增加 `list` / `get` / `confirm` / `inbound` / `exportContract` / `getInvoiceUrl` 方法。

### 修改文件

- `frontend/src/router/index.ts`：在 `implementedRoutes` 中注册 `/purchases`。
- `frontend/src/router/businessRoutes.ts`：将 `purchase` 的 `implemented` 改为 `true`。

## 3. 数据流

### 列表加载

1. `PurchaseManagement` 挂载 → `purchaseApi.list({ page, page_size, keyword, status })`。
2. 后端返回列表（含 `po_no`、`pi_no`、`supplier_name`、`total_amount`、`currency`、`status`、`created_at`）。
3. 渲染 `el-table`，状态着色：已入库绿、已确认橙、草稿灰。

### 确认/入库

- 确认：`purchaseApi.confirm(poId)` → `POST /api/purchase-orders/{id}/confirm`。
- 入库：`purchaseApi.inbound(poId)` → `POST /api/purchase-orders/{id}/inbound`。
- 成功后刷新列表。

### 查看发票

- 调用 `purchaseApi.getInvoiceUrl(poId)` → `GET /api/purchase-orders/{id}/invoice`。
- 返回 URL 后用 `window.open` 或图片预览 Dialog 打开。
- 如果发票不存在，显示空提示。

### 导出合同

- 调用 `purchaseApi.exportContract(poId)` → `GET /api/export/purchase/{poId}/contract`。
- 后端返回 Excel 文件流，前端触发下载。
- 同时显示 `ElMessage.success('合同已导出')`。

## 4. 错误处理

- 网络失败：`ElMessage.error('操作失败：<reason>')`。
- 4xx：`detail` 透传 toast。
- 发票不存在：显示空状态，不报错。

## 5. 手动验收

- 采购订单列表正常加载，状态着色正确。
- 确认按钮点击后状态更新。
- 入库按钮点击后状态更新。
- 发票按钮能打开/预览发票。
- 合同按钮能下载 Excel。
- 刷新按钮能重新加载列表。
