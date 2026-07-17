# PI Manager 项目上下文 Spec

> 给 AI / 协作者使用的精简项目地图。重点记录目录结构、启动方式、核心模块关系、分类编码规则、常用接口约定、关键字段含义与改动偏好。

---

## 1. 仓库与目录结构

当前主要开发目录是：

`D:\TraeProjects\PI Manager\worktrees\frontend-repo`

这是前端和后端共存的主工作树：

```text
frontend-repo/
├─ backend/                 # FastAPI 后端
│  ├─ app/                  # database.py 等基础设施
│  ├─ crud/                 # 数据访问与业务查询逻辑
│  ├─ models/               # SQLAlchemy ORM
│  ├─ routers/              # FastAPI 路由
│  ├─ schemas/              # Pydantic schema
│  ├─ exporters/            # PI / CI / PL / 合同等导出
│  ├─ migrations/           # 一次性迁移脚本和迁移路由
│  ├─ config/               # 静态配置
│  ├─ data/                 # SQLite 数据库
│  ├─ uploads/              # 上传图片
│  ├─ main.py               # FastAPI 入口，路由集中注册
│  └─ run.py / run.bat
└─ frontend/                # Vue 3 + Vite 前端
   ├─ src/
   │  ├─ api/               # API 封装
   │  ├─ views/             # 页面
   │  ├─ components/        # 业务组件
   │  ├─ composables/       # 组合式逻辑
   │  ├─ constants/         # 跨 SFC 共享常量
   │  ├─ stores/            # Pinia store
   │  ├─ router/            # vue-router
   │  ├─ styles/            # 全局样式
   │  └─ types/             # TS 类型
   ├─ package.json
   └─ vite.config.ts
```

历史/相关工作树可能还包括：

| 路径 | 角色 | 备注 |
|---|---|---|
| `worktrees\frontend-repo` | 当前 Web 主开发工作树 | Vue 3 + FastAPI |
| `worktrees\master-clean` | PyQt 桌面客户端 | QWebEngineView 加载 Web 前端 |
| `worktrees\PI-Manager-System` | 旧版/历史参考 | 通常不直接修改 |

---

## 2. 启动方式

### 2.1 后端 FastAPI

```powershell
cd "D:\TraeProjects\PI Manager\worktrees\frontend-repo\backend"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

默认后端地址通常是 `http://127.0.0.1:8000`。

后端入口：

- `backend/main.py`
- `Base.metadata.create_all(bind=engine)` 会自动建表
- 上传目录：`backend/uploads/`
- 图片静态访问挂载：`/images`

### 2.2 前端 Vue

```powershell
cd "D:\TraeProjects\PI Manager\worktrees\frontend-repo\frontend"
npm install
npm run dev
```

常用脚本：

| 命令 | 说明 |
|---|---|
| `npm run dev` | Vite 开发服务 |
| `npm run build` | `vue-tsc && vite build` |
| `npm run test` | Vitest |

---

## 3. 核心模块关系

业务上以客户、客户产品、PI 订单、采购、出货、收付款为主线。

```text
CrmCustomer 客户
  └─ 1:N PrdCustomerProduct 客户产品
        ├─ category_id -> PrdProductCategory.code
        ├─ codes -> PrdCustomerProductCode
        └─ oes -> PrdCustomerProductOE

PiProformaInvoice PI/订单
  └─ 1:N PiProformaInvoiceItem PI 明细
        └─ product_id -> PrdCustomerProduct.id

PoPurchaseOrder 采购单
  └─ 1:N PoPurchaseOrderItem 采购明细

Shipment 出货
  └─ shipment item 关联 PI 明细

ArCustomerPayment 客户收款
  └─ pi_id -> PiProformaInvoice.id
```

模块对照：

| 业务概念 | 后端模型/路由 | 前端位置 |
|---|---|---|
| 客户 | `CrmCustomer`, `routers/customer.py` | `views/customer/` |
| 客户产品 | `PrdCustomerProduct`, `routers/customer_product.py` | `views/product/ProductManagement.vue` |
| 产品编辑 | `crud/customer_product.py` | `components/order/ProductEditDialog.vue` |
| 产品类别 | `PrdProductCategory`, `routers/product_category.py` | `constants/productCategories.ts` |
| 订单/PI | `PiProformaInvoice`, `routers/pi.py`, `routers/bff.py` | `views/order/`, `views/pi/` |
| 采购 | `PoPurchaseOrder`, `routers/purchase.py` | `views/purchase/` |
| 出货 | `models/shipment.py`, `routers/shipment.py` | `views/shipment/` |
| 收付款 | `routers/payment.py` | `views/payment/` |

重要约定：

- 产品跟随客户，不是全局产品主数据。客户产品表是 `prd_customer_product`。
- PI 明细保存图片时，要注意 `pi_proforma_invoice_item.temp_image` 和 `prd_customer_product.image_url` 的同步关系。
- 前端编辑 PI 明细的核心复用逻辑在 `frontend/src/composables/useProductEdit.ts`。

---

## 4. 产品分类规则

分类使用两级编码：

| 大类 code | 名称 |
|---|---|
| `C` | 汽配件 |
| `F` | 办公家具 |
| `B` | 百货类 |

子类：

| 大类 | 子类 code | 名称 |
|---|---|---|
| `C` | `C01` | 发动机 |
| `C` | `C02` | 曲轴 |
| `C` | `C03` | 刹车片 |
| `C` | `C09` | 杂项 |
| `F` | `F01` | 椅子类 |
| `F` | `F02` | 桌子类 |
| `F` | `F03` | 柜子类 |
| `F` | `F88` | 工程定制 |
| `B` | `B00` | 百货类 |

字段约定：

- `prd_product_category.code` 是业务分类编码。
- `prd_product_category.parent_id` 存的是上级分类的 `code`，不是数字 ID。
- `prd_customer_product.category_id` 存分类 `code`，例如 `C01`。

兜底常量：

- 前端：`frontend/src/constants/productCategories.ts`
- 后端产品筛选：`backend/crud/customer_product.py` 的 `FALLBACK_CATEGORY_CHILDREN`

新增或调整分类时，需要同步数据库数据和兜底常量。

### 4.1 大类筛选约定

`GET /api/customer-products` 的 `category_code` 支持传大类或子类：

- 传 `C01`：只筛选 `category_id = C01`
- 传 `C`：后端展开为 `C, C01, C02, C03, C09` 后查询

相关实现：

- 前端选择器：`frontend/src/views/product/ProductManagement.vue`
- API 封装：`frontend/src/api/products.ts`
- 后端查询：`backend/crud/customer_product.py`

---

## 5. 常用接口约定

前端端点统一维护在 `frontend/src/api/endpoints.ts`。新增或调整接口时，优先更新 `endpoints.ts`，再同步本节。

`API_HOST` 当前默认值：`https://piapi.wakabashia.tj.cn`。

### 5.1 认证

对应 `AUTH`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/auth/login` | 登录 |
| `POST` | `/api/auth/logout` | 登出 |
| `GET` | `/api/auth/me` | 当前用户 |

### 5.2 客户 / 供应商

对应 `CUSTOMERS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/customers/` | 客户列表 |
| `GET` | `/api/customers/{id}` | 客户详情 |
| `POST` | `/api/customers/` | 创建客户 |
| `PUT` | `/api/customers/{id}` | 更新客户 |
| `DELETE` | `/api/customers/{id}` | 删除客户 |
| `PATCH` | `/api/customers/{id}/status` | 切换客户状态 |
| `GET` | `/api/customers/search` | 搜索客户 |
| `GET` | `/api/customers/{id}/contacts` | 客户联系人 |
| `POST` | `/api/customers/{id}/contacts` | 创建联系人 |
| `PUT` | `/api/customers/{id}/contacts/{cid}` | 更新联系人 |
| `DELETE` | `/api/customers/{id}/contacts/{cid}` | 删除联系人 |

对应 `SUPPLIERS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/suppliers/` | 供应商列表 |
| `GET` | `/api/suppliers/{id}` | 供应商详情 |
| `POST` | `/api/suppliers/` | 创建供应商 |
| `PUT` | `/api/suppliers/{id}` | 更新供应商 |
| `DELETE` | `/api/suppliers/{id}` | 删除供应商 |
| `GET` | `/api/suppliers/provinces` | 供应商省份列表 |
| `GET` | `/api/suppliers/cities/{province}` | 指定省份城市 |

### 5.3 客户产品 / 分类

对应 `CUSTOMER_PRODUCTS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/customer-products` | 客户产品列表 |
| `GET` | `/api/customer-products/{id}` | 单个客户产品 |
| `GET` | `/api/customer-products/search` | 搜索客户产品（OE号/客户型号/产品名称，支持 customer_id 过滤） |
| `POST` | `/api/customer-products/{id}/oes/bulk-sync` | 差量同步一个客户产品的 OE 号列表 |
| `POST` | `/api/customer-products` | 创建客户产品 |
| `PUT` | `/api/customer-products/{id}` | 更新客户产品 |
| `DELETE` | `/api/customer-products/{id}` | 删除客户产品 |

`GET /api/customer-products` 查询参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page` | int | 页码，从 1 开始 |
| `page_size` | int | 每页数量 |
| `search` | string | 模糊搜索 |
| `customer_id` | int | 按客户筛选 |
| `category_code` | string | 分类编码，支持大类或子类 |

返回：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

### 5.3.1 产品搜索服务字段说明

| 字段 | 来源 | 说明 |
|---|---|---|
| `product_name` | PI item.detail_desc > PrdCustomerProduct.product_name | 用户最近编辑的产品名称，优先取 PI item |
| `customer_model` | PI item.customer_model > PrdCustomerProduct.customer_model | 用户最近编辑的客户型号，优先取 PI item |
| `oes` | PrdCustomerProductOE | 主 OE 排第一；bulk-sync 时有序去重 |
| `matched_in` | 搜索命中字段 | 数组，指示该结果命中了哪些字段 |
| `match_score` | 加权分 | customer_model 精确=100，模糊=80；OE=50；product_name=60；detail_desc=30 |

对应 `PRODUCT_CATEGORIES`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/product-categories/?status=1` | 获取启用分类 |
| `GET` | `/api/product-categories/{id}` | 分类详情 |
| `POST` | `/api/product-categories/` | 创建分类 |
| `PUT` | `/api/product-categories/{id}` | 更新分类 |
| `DELETE` | `/api/product-categories/{id}` | 删除分类 |
| `GET` | `/api/product-categories/next-code` | 获取下一个分类编码 |

对应 `PRODUCT_CUSTOMER`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/product-customer/search` | 兼容产品搜索 |

### 5.4 订单 / PI

对应 `ORDERS_BFF`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/bff/orders` | 订单列表聚合接口 |
| `GET` | `/api/bff/orders/{id}` | BFF 订单详情 |
| `POST` | `/api/bff/orders` | 创建订单 |
| `PUT` | `/api/bff/orders/{id}` | 更新订单 |
| `DELETE` | `/api/bff/orders/{id}` | 删除订单 |
| `POST` | `/api/bff/orders/{order_id}/import-items` | 导入订单明细 |
| `GET` | `/api/bff/orders/dashboard` | 订单看板统计 |
| `GET` | `/api/bff/orders/{order_id}/full-detail` | 订单完整详情 |
| `POST` | `/api/orders/{order_id}/supplement-items` | 补充订单明细 |
| `POST` | `/api/orders/import` | 订单导入 |

对应 `PI`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/pi/{id}` | PI 详情 |
| `POST` | `/api/pi/` | 创建 PI |
| `DELETE` | `/api/pi/{id}` | 删除 PI |
| `PUT` | `/api/pi/{pi_id}/status` | 更新 PI 状态 |
| `POST` | `/api/pi/{order_id}/generate-pi` | 生成 PI |
| `GET` | `/api/pi/{order_id}/formal-record/exists` | 查询正式记录是否存在 |
| `POST` | `/api/pi/{order_id}/formal-record` | 保存正式记录 |
| `POST` | `/api/pi/{pi_id}/inbound-batch` | PI 批量入库 |
| `GET` | `/api/pi/{order_id}/payments` | PI 付款/收款信息 |

对应 `PI_ITEMS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `PUT` | `/api/pi/items/{item_id}` | 更新 PI 明细 |
| `DELETE` | `/api/pi/items/{item_id}` | 删除 PI 明细 |
| `POST` | `/api/pi/items/{item_id}/inbound` | PI 明细入库 |

### 5.5 采购

对应 `PURCHASE`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/purchase-orders/1688` | 创建线上 1688 采购单 |
| `POST` | `/api/purchase-orders` | 创建线下采购单 |
| `GET` | `/api/purchase-orders` | 采购单列表 |
| `POST` | `/api/purchase-orders/{id}/confirm` | 确认采购单 |
| `POST` | `/api/purchase-orders/{id}/inbound` | 采购入库 |
| `POST` | `/api/purchase-orders/{id}/invoice` | 采购开票 |
| `GET` | `/api/purchase-orders/product/{product_id}/latest` | 产品最近采购记录 |
| `GET` | `/api/purchase-orders/1688/recent-urls?product_id={product_id}&limit={limit}` | 最近 1688 链接 |
| `GET` | `/api/export/purchase/{id}/contract` | 导出采购合同 |

### 5.6 出货

对应 `SHIPMENTS`：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/shipments/` | 出货列表 |
| `GET` | `/api/shipments/{id}` | 出货详情 |
| `GET` | `/api/shipments/shippable-items` | 可出货明细 |
| `POST` | `/api/shipments/from-orders` | 从订单创建出货 |
| `POST` | `/api/shipments/{id}/confirm` | 确认出货 |

### 5.7 收款

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/payments/receivables` | 收款列表/BFF 聚合 |
| `GET` | `/api/payments/receivables/by-pi/{pi_id}` | 指定 PI 的收款明细 |
| `GET` | `/api/payments/receivables/{id}` | 收款详情 |

注意：`/api/payments/receivables/by-pi/{pi_id}` 返回字段和 BFF 收款列表字段不完全一致，不要混用。

### 5.8 图片 / 迁移

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/images/upload` | 上传图片，`multipart/form-data` |
| `GET` | `/images/{filename}` | 访问上传图片 |
| `POST` | `/api/migrations/sync-product-images` | 同步 PI 明细图片到客户产品主图 |

---

## 6. 关键数据表字段

### 6.1 `prd_customer_product`

| 字段 | 含义 |
|---|---|
| `id` | 客户产品 ID |
| `customer_id` | 所属客户 |
| `system_code` | 系统产品编号 |
| `product_name` | 产品名称 |
| `customer_model` | 客户型号 |
| `category_id` | 分类 code，例如 `C01` |
| `image_url` | 主图 URL |
| `sub_images` | 副图 URL JSON 数组 |
| `brand` | 品牌 |
| `specifications` | 规格 |
| `is_active` | 是否启用/未软删 |
| `is_temporary` | 是否临时产品 |
| `deleted_at` | 软删除时间 |

### 6.2 `prd_product_category`

| 字段 | 含义 |
|---|---|
| `id` | 数据库自增 ID |
| `code` | 分类业务编码 |
| `name` | 分类名称 |
| `parent_id` | 上级分类 code，空表示大类 |
| `status` | 1=启用，0=停用 |
| `sort_order` | 排序 |

### 6.3 `pi_proforma_invoice_item`

| 字段 | 含义 |
|---|---|
| `id` | PI 明细 ID |
| `pi_id` | 所属 PI |
| `product_id` | 关联客户产品 |
| `quantity` | 数量 |
| `unit_price` | 销售单价 |
| `purchase_price` | 采购价 |
| `shipping_fee` | 运费 |
| `misc_fee` | 杂费 |
| `temp_image` | 明细临时图片 |
| `temp_category_id` | 临时分类 |
| `is_temporary` | 是否临时产品 |
| `is_deleted` | 是否软删 |

### 6.4 `ar_customer_payment`

| 字段 | 含义 |
|---|---|
| `receipt_no` | 水单号 |
| `pi_id` | 关联 PI |
| `amount` | 应收金额 |
| `handling_fee` | 手续费 |
| `actual_amount` | 实收金额 |
| `payment_date` | 付款日期 |
| `water_image` | 水单图片 |
| `is_fully_paid` | 是否收齐 |

---

## 7. 改动偏好

1. 优先保持现有架构：路由薄、CRUD 厚，前端 API 封装放在 `src/api/`。
2. 业务规则和查询语义优先放后端，前端主要负责展示和交互。
3. bug 修复尽量小范围，不顺手重构无关代码。
4. 共享常量不要只写在某个 SFC 的 `<script setup>` 中，需要跨页面复用时放到 `src/constants/`。
5. 分类相关改动要同步前后端兜底常量。
6. 图片保存相关改动要检查 PI 明细图片和客户产品主图的同步。
7. PyQt 宿主兼容性要特别小心：
   - 避免给 `el-dialog` 加 `append-to-body`。
   - 避免覆盖 Element Plus overlay 为不透明白色。
   - PyQt 看不到更新时，可能需要清除 QWebEngine 前端缓存。

---

## 8. 已知坑位

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 大类筛选无结果 | 产品只存子类，后端精确匹配大类 | 后端展开大类到子类列表 |
| 分类下拉为空 | `prd_product_category` 表为空 | 使用前端/后端 fallback 分类 |
| 产品管理没有图片但 PI 明细有 | 只写了 `temp_image` | 同步写 `prd_customer_product.image_url` |
| PyQt 弹窗黑屏 | `el-dialog append-to-body` 或 overlay 层问题 | 去掉相关设置，尽量用默认 Element Plus 行为 |
| PyQt 看不到前端更新 | QWebEngine 缓存 | 清除客户端前端缓存 |

---

## 9. 相关文档

- `docs/vue-config-guide.md`
- `docs/superpowers/plans/`
- `docs/superpowers/specs/`
