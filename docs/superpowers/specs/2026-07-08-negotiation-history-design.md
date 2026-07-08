# 议价沟通历史与报价单导出 设计规格

> **日期**：2026-07-08
> **状态**：草稿，待评审

---

## 1. 背景与目标

`ProductEditDialog.vue` 销售细节区的四个字段（`customer_demand` / `reply` / `confirm_info` / `quote_remark`）目前无法持久化。其中前两个字段是对话式的多轮沟通，需要支持完整历史记录；后两个为普通字符串。

同时，报价单（Quotation）和 PI 单（Proforma Invoice）是独立文档，报价单用于与客户往来确认，PI 单为正式订单记录，两者均需展示谈判往来。

---

## 2. 数据模型

### 2.1 新增 JSON 列

在 `PiProformaInvoiceItem` 模型新增字段：

```python
negotiation_history = Column(Text, nullable=True)  # 存储 JSON 数组
```

JSON 结构（每轮为 customer demand + reply 绑定为一组）：

```json
[
  {
    "demand": "客户要求降价到 $10",
    "reply": "可以，但需增加数量",
    "demand_at": "2026-07-08T10:00:00",
    "reply_at": "2026-07-08T14:30:00"
  },
  {
    "demand": "客户同意增加数量",
    "reply": "已确认，最终价格 $9.5",
    "demand_at": "2026-07-09T09:00:00",
    "reply_at": "2026-07-09T11:00:00"
  }
]
```

**约束**：
- `demand` 字段填写后可补充，不可删除；`reply` 可随时编辑
- `demand_at` 自动生成（UTC），`reply_at` 在填写 reply 并保存时自动生成
- 全量读写（每次保存传完整数组），无字段级锁，适合低并发场景

### 2.2 confirm_info 和 quote_remark

这两个字段为普通字符串，直接在 `PiProformaInvoiceItem` 新增两列：

```python
confirm_info = Column(Text, nullable=True)
quote_remark = Column(Text, nullable=True)
```

---

## 3. BFF 层修改

### 3.1 `full-detail` 接口返回调整

`/api/bff/orders/{order_id}/full-detail` 中，`_build_order_detail_item` 已在 `image_url` 处理中新增 `request` 参数，同理处理新增字段：

```python
negotiation_history=json.loads(item.negotiation_history) if item.negotiation_history else [],
confirm_info=_to_str(item.confirm_info),
quote_remark=_to_str(item.quote_remark),
```

### 3.2 更新 `update_pi_item` 处理新字段

`crud/pi.py` 中 `update_pi_item` 函数新增处理：

```python
if 'negotiation_history' in update_data:
    db_item.negotiation_history = json.dumps(update_data['negotiation_history'])
    print(f"[DEBUG] update_pi_item: 更新 negotiation_history")
if 'confirm_info' in update_data:
    db_item.confirm_info = update_data['confirm_info']
if 'quote_remark' in update_data:
    db_item.quote_remark = update_data['quote_remark']
```

---

## 4. 前端接口

### 4.1 类型定义

在 `orderSummary.d.ts` 的 `OrderDetailItem` 新增：

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

### 4.2 API 层

`ProductEditForm` 接口新增三个字段（类型同上），`initFromItem` 读取赋值。

---

## 5. UI 交互

### 5.1 表格列显示

`customer_demand` / `reply` 列在 `OrderDetailPanel` 中显示策略：
- 显示最新一轮的 `reply`（若 reply 为空则显示 demand 截断文本）
- 若数组为空，显示占位符 `"-"`

`confirm_info` 和 `quote_remark` 直接在表格列展示。

### 5.2 双击打开谈判记录 Dialog

双击 `customer_demand` 或 `reply` 列单元格 → 弹出 `NegotiationDialog.vue`（`ProductEditDialog` 保持打开）。

#### NegotiationDialog.vue 布局

- 标题：产品名称 + "议价沟通记录"
- 轮次列表（el-scrollbar，可滚动）：
  - 每轮显示：demand 内容 + demand_at 时间 | reply 内容 + reply_at 时间
  - 若 reply 未填写，该轮高亮提示"待答复"
- 底部"添加需求"按钮
- Dialog 右上角有关闭按钮（只关闭自己，不影响父 dialog）

#### 添加需求流程

1. 点击"添加需求"→ 新增一轮（demand_at = now UTC），reply_at = null
2. demand 输入框获得焦点，用户填写
3. 点击"保存"→ PUT `negotiation_history` 整体回传
4. 新轮出现在列表顶部

#### 编辑/补充答复

- 已存在轮的 reply 字段可直接编辑
- reply 首次填写并保存时，自动写入 reply_at = now UTC
- reply 后续修改不改变 reply_at

---

## 6. 报价单导出

### 6.1 新增报价单导出路由

`POST /api/export/quotation/{pi_id}` → 生成报价单 Excel，逻辑与 `PIExporter` 类似但：
- 文件名：`Quotation_{pi_no}_{date}.xlsx`
- 包含"议价沟通记录"列或备注区，展示该产品所有轮次的需求+答复历史
- 客户名称、交货条款等字段与 PI 单一致

### 6.2 报价单模板调整

`QuoteExporter`（新建）或在 `PIExporter` 中加分支逻辑，生成含谈判历史的报价单。

### 6.3 PI 单导出

`PIExporter` 不变，PI 单保留谈判历史作为内部记录，不强制展示给客户（PIExporter 不读取 negotiation_history）。

---

## 7. 数据库迁移

需要 Alembic 迁移：

```python
# revision
op.add_column('pi_proforma_invoice_item',
    Column('negotiation_history', Text, nullable=True))
op.add_column('pi_proforma_invoice_item',
    Column('confirm_info', Text, nullable=True))
op.add_column('pi_proforma_invoice_item',
    Column('quote_remark', Text, nullable=True))
```

---

## 8. 暂未涵盖（YAGNI）

- 谈判记录的历史回滚/撤销
- 邮件通知触发（客户提交新需求时）
- 谈判轮次的手动排序

---

## 9. 文件变更清单

| 文件 | 操作 |
|------|------|
| `backend/models/pi.py` | 新增 `negotiation_history`, `confirm_info`, `quote_remark` 列 |
| `backend/crud/pi.py` | `update_pi_item` 新增三个字段的处理逻辑 |
| `backend/routers/bff.py` | `_build_order_detail_item` 返回新字段；`_absolute_url` 已实现 |
| `backend/routers/export.py` | 新增 `POST /export/quotation/{pi_id}` |
| `backend/exporters/quote_exporter.py` | 新建，报价单 Excel 生成器 |
| `frontend/src/types/orderSummary.d.ts` | `OrderDetailItem` 新增三个字段类型 |
| `frontend/src/api/orderSummary.ts` | 无需变更（saveField 通过 PUT /api/pi/items/{id} 通用接口） |
| `frontend/src/components/order/ProductEditDialog.vue` | `ProductEditForm` 新增字段；`initFromItem` 读取；`confirm_info` / `quote_remark` 用 FieldInput 展示 |
| `frontend/src/components/order/NegotiationDialog.vue` | 新建，议价历史 Dialog |
| `frontend/src/views/order/OrderDetailPanel.vue` | `customer_demand` / `reply` 列双击打开 NegotiationDialog；`confirm_info`/`quote_remark` 列直接展示 |
| 数据库迁移 | 新增 migration 文件 |
