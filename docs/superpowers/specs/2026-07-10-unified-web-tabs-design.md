# 统一 Web 容器替换 PyQt 业务 Tab 设计

> 状态：草案（待用户最终审阅）
> 日期：2026-07-10
> 适用版本：pyqt-to-web-migration 客户端 + frontend-repo SPA
> 替代：散落在 PyQt 主窗口 `MainWindow` 的 12 个业务 Tab + 已存在的 `_create_web_order_tab`

## 1. 目标与范围

### 1.1 一句话目标
把 PyQt 客户端 12 个业务入口全部收敛到同一个 Vue SPA，客户端只保留稳定路由契约，实现的页面由服务器前端热更新，**不再需要更新客户端二进制**。

### 1.2 范围

**包含**
- PyQt 左侧 12 个菜单（产品 / 客户 / 供应商 / 报价 / PI / 采购 / 出货 / 客户付款 / 供应商付款 / 库存 / 订单总表 / Web 订单）。
- 单一 `WebContainerView` 渲染这些菜单对应的 Vue 路由。
- 一份 `ComingSoonView` 占位页（统一模板）。
- 客户端 `TAB_ROUTES` 字典与 Vue `router/index.ts` 的稳定契约。

**不包含**
- 旧 PyQt 业务类（订单产品 Dialog、供应商付款编辑等）的清理工作，本轮只迁移外壳。
- 任何具体业务模块的真实页面实现，后续轮次按模块上线。
- 出货、收款、订单这类已实现的页面继续保留原实现。

### 1.3 成功标准
1. 用户在 PyQt 内点击任意 12 个菜单，跳转到对应 SPA 路径，不会因为还没实现出现空白或崩溃。
2. 服务器发布任一未实现模块（例：`/products` 真实页面）后，PyQt 用户刷新或重启即可看到，不需客户端升级。
3. PyQt `main.py` 中不再创建 12 个独立 `QStackedWidget` 业务页面，仅留下一个 `WebContainerView`。
4. `npm run build` / `npm test` 通过；后端 `py_compile` 不报错。

---

## 2. 架构与文件边界

### 2.1 客户端（PyQt）

```text
client/
  main.py
    - TAB_ROUTES: dict[str, str]                    # 菜单键 -> 路径
    - switch_tab(key): 仅调用 navigate_to(self._web_view, TAB_ROUTES[key])
    - init_ui(): 移除 QStackedWidget 业务子类
  web_container/web_view.py
    + navigate_to(self, path): QUrl(remote + path), load(url)
```

`TAB_ROUTES`（稳定契约，发布后基本不变）：

| key           | path                  |
|---------------|-----------------------|
| products      | `/products`           |
| customers     | `/customers`          |
| suppliers     | `/suppliers`          |
| quotes        | `/quotes`             |
| pi            | `/pi`                 |
| purchase      | `/purchases`          |
| shipment      | `/shipments`          |
| customer_payment | `/payments/customer` |
| supplier_payment | `/payments/supplier` |
| inventory     | `/inventory`          |
| order_summary | `/orders`             |
| web_order     | `/orders`             |

说明：
- `order_summary` 与 `web_order` 都指向 `/orders`，避免重复入口，UI 上可合并显示。
- `routes` 路径与服务器真实模块命名同语义，未来不再调整。

### 2.2 前端（Vue 3 + Vite）

```text
frontend/src/
  views/misc/ComingSoonView.vue          # 统一占位
  router/comingSoonRoutes.ts             # 占位路由与菜单映射
  router/index.ts                        # 注册：占位 + 已实现
```

`router/index.ts` 关键变化：
- 不再写 `/menu/:key` 这类动态临时路由。
- `/products` 这类已实现路由直接指向真实页面，否则指向 `ComingSoonView`。
- 兜底路由 `*` 指向 `ComingSoonView`，防止裸 404。

`ComingSoonView.vue`：
- 接收 `moduleKey` prop。
- 调用 `GET /api/coming-soon/:key` 拉“模块名 / 负责人 / 数据来源说明 / 上次更新时间”。
- 渲染一张“开发中”卡片 + “刷新” + “返回上级（订单总表）”按钮。

---

## 3. 数据流

### 3.1 菜单点击

1. PyQt `MainWindow` 接收到菜单点击 → `switch_tab('products')`。
2. `switch_tab` 查表得 `path = '/products'`。
3. 调用 `self._web_view.navigate_to('/products')`。
4. `WebContainerView.load(QUrl(remote + path))`，SPA 路由切换。

### 3.2 SPA 路由匹配

1. Vue Router 命中 `/products`：
   - 已实现 → `ProductsView`（开发后续轮次实现，本轮只留占位）。
   - 未实现 → `ComingSoonView` 注入 `moduleKey='products'`。
2. `ComingSoonView` 在 `onMounted` 中：
   - 调 `GET /api/coming-soon/products`。
   - 失败则回退本地静态文案，不阻塞渲染。

### 3.3 热更新路径

- 服务器把 `/products` 的真实页面部署至 `https://piapi.wakabashia.tj.cn/products`。
- 客户端刷新 `WebContainerView` 或整应用重启。
- 路由契约未变，PyQt 客户端无需重新发布。

### 3.4 错误处理

| 场景 | 处理 |
|------|------|
| 前端地址失效 | 已有 30s 重连；增加托盘 toast。 |
| 服务器返回 5xx | SPA 在网络层显示加载失败，留“刷新”按钮。 |
| 占位接口失败 | `ComingSoonView` 降级显示默认文案。 |
| 未识别的 SPA 路径 | `*` 兜底路由解析为 `ComingSoonView`，`moduleKey` 推断自路径首段。 |

---

## 4. 错误处理与测试

### 4.1 测试策略

| 级别 | 用例 |
|------|------|
| 前端单元 | `TAB_ROUTES` key 不重复且全部非空。 |
| 前端构建 | `npm run build` 通过；`npm test` 通过。 |
| 手动 | 12 个菜单点击跳转、刷新仍可加载、模拟服务器发布后能在客户端生效。 |
| 后端冒烟 | `GET /api/coming-soon/:key` 返回 JSON 含 module_key/owner/source/updated_at，缺字段回退默认文案。 |

### 4.2 手动验收清单

- [ ] 12 个菜单点击均能跳转到 SPA 路径。
- [ ] 切换菜单无白屏闪烁（同一 `WebContainerView`）。
- [ ] 服务器临时关闭 → 仍能显示占位，不崩。
- [ ] 服务器发布 `/products` → 客户端刷新可见。
- [ ] 占位页能展示模块名、负责人、本期进度、最近更新、原始 PyQt 入口。

---

## 5. 后续轮次

1. 实现 `/api/coming-soon/:key`（后端不需要任何数据库表，从静态 JSON 返回）。
2. 在 Vue router 中将 `/products` 暂时指向占位页面。
3. 把 `/products` 等陆续替换为真实业务页面（每一页一次一个 PR）。
4. 客户端 `TAB_ROUTES` 永久不变。
