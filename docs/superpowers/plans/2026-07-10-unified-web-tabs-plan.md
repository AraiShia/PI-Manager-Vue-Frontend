# 统一 Web 容器替换 PyQt 业务 Tab 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 PyQt 主窗口的 12 个业务入口收敛到单一 `WebContainerView`，并为尚未迁移的模块提供稳定的 Vue 占位路由，使后续服务器发布真实页面时无需升级客户端。

**架构：** PyQt 只维护菜单键到最终业务路径的稳定映射，并复用一个浏览器实例导航。Vue Router 注册全部最终路径：订单、客户收款和出货继续使用真实页面，其余路径指向统一占位组件。旧 PyQt 页面实现暂不删除，只从主窗口初始化与切换路径中退出，便于必要时回退。

**技术栈：** Python 3、PySide6 QtWebEngine、Vue 3、Vue Router 4、TypeScript、Vite、Vitest、pytest

---

## 文件结构

### 创建
- `frontend/src/router/businessRoutes.ts`：业务菜单元数据与稳定路径契约，供路由和测试共用。
- `frontend/src/views/misc/ComingSoonView.vue`：未实现模块的统一占位页面。
- `frontend/src/router/__tests__/businessRoutes.spec.ts`：验证 12 个菜单键、路径唯一性和真实/占位模块分类。
- `tests/client/test_web_tab_routes.py`：验证 PyQt 客户端菜单路由契约和单容器导航。

### 修改
- `frontend/src/router/index.ts`：注册已实现页面、占位页面和 404 兜底。
- `client/main.py`：增加 `TAB_ROUTES`，只创建一个 `WebContainerView`，菜单切换改为 URL 导航。
- `client/web_container/web_view.py`：规范 URL 拼接，避免重复斜杠并支持刷新当前页面。

### 保留不动
- `client/widgets/**`、`client/dialogs/**`：旧 PyQt 业务实现本轮不删除。
- 后端：占位页元数据先由前端静态配置提供，不新增无必要的 `/api/coming-soon/:key` 接口；真实模块上线时直接替换路由组件。

---

### 任务 1：建立前端业务路由契约

**文件：**
- 创建：`frontend/src/router/businessRoutes.ts`
- 创建：`frontend/src/router/__tests__/businessRoutes.spec.ts`

- [ ] **步骤 1：编写失败的路由契约测试**

```ts
import { describe, expect, it } from 'vitest'
import { BUSINESS_ROUTES } from '../businessRoutes'

const expectedKeys = [
  'products', 'customers', 'suppliers', 'quotes', 'pi', 'purchase',
  'shipment', 'customer_payment', 'supplier_payment', 'inventory',
  'order_summary', 'web_order',
]

describe('BUSINESS_ROUTES', () => {
  it('covers every PyQt business menu', () => {
    expect(BUSINESS_ROUTES.map(item => item.key)).toEqual(expectedKeys)
  })

  it('uses stable absolute paths', () => {
    expect(BUSINESS_ROUTES.every(item => item.path.startsWith('/'))).toBe(true)
    expect(BUSINESS_ROUTES.find(item => item.key === 'shipment')?.path).toBe('/shipments')
    expect(BUSINESS_ROUTES.find(item => item.key === 'customer_payment')?.path).toBe('/payments/customer')
  })

  it('marks currently implemented modules', () => {
    const implemented = BUSINESS_ROUTES.filter(item => item.implemented).map(item => item.key)
    expect(implemented).toEqual(['shipment', 'customer_payment', 'order_summary', 'web_order'])
  })
})
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
npm test -- src/router/__tests__/businessRoutes.spec.ts
```

预期：FAIL，提示找不到 `../businessRoutes`。

- [ ] **步骤 3：实现最小路由元数据**

```ts
export interface BusinessRouteMeta {
  key: string
  path: string
  title: string
  source: string
  owner: string
  implemented: boolean
}

export const BUSINESS_ROUTES: readonly BusinessRouteMeta[] = [
  { key: 'products', path: '/products', title: '产品管理', source: '原 PyQt 产品管理', owner: '产品模块', implemented: false },
  { key: 'customers', path: '/customers', title: '客户管理', source: '原 PyQt 客户管理', owner: '客户模块', implemented: false },
  { key: 'suppliers', path: '/suppliers', title: '供应商管理', source: '原 PyQt 供应商管理', owner: '供应商模块', implemented: false },
  { key: 'quotes', path: '/quotes', title: '报价管理', source: '原 PyQt 报价管理', owner: '报价模块', implemented: false },
  { key: 'pi', path: '/pi', title: 'PI 管理', source: '原 PyQt PI 管理', owner: 'PI 模块', implemented: false },
  { key: 'purchase', path: '/purchases', title: '采购管理', source: '原 PyQt 采购管理', owner: '采购模块', implemented: false },
  { key: 'shipment', path: '/shipments', title: '出货管理', source: 'Web 出货管理', owner: '出货模块', implemented: true },
  { key: 'customer_payment', path: '/payments/customer', title: '客户付款', source: 'Web 收款管理', owner: '收款模块', implemented: true },
  { key: 'supplier_payment', path: '/payments/supplier', title: '供应商付款', source: '原 PyQt 供应商付款', owner: '付款模块', implemented: false },
  { key: 'inventory', path: '/inventory', title: '库存管理', source: '原 PyQt 库存管理', owner: '库存模块', implemented: false },
  { key: 'order_summary', path: '/orders', title: '订单总表', source: 'Web 订单总表', owner: '订单模块', implemented: true },
  { key: 'web_order', path: '/orders', title: 'Web 订单', source: 'Web 订单总表', owner: '订单模块', implemented: true },
]
```

说明：`order_summary` 和 `web_order` 有意共用 `/orders`，因此测试只校验菜单键唯一，不强制路径唯一。

- [ ] **步骤 4：运行测试并确认通过**

运行：

```powershell
npm test -- src/router/__tests__/businessRoutes.spec.ts
```

预期：1 个测试文件通过，3 个测试通过。

- [ ] **步骤 5：检查改动**

运行：

```powershell
git diff -- frontend/src/router/businessRoutes.ts frontend/src/router/__tests__/businessRoutes.spec.ts
```

预期：仅包含业务路由契约和测试；不提交 commit，除非用户明确要求。

---

### 任务 2：实现占位页面与最终业务路由

**文件：**
- 创建：`frontend/src/views/misc/ComingSoonView.vue`
- 修改：`frontend/src/router/index.ts`
- 修改：`frontend/src/router/__tests__/businessRoutes.spec.ts`

- [ ] **步骤 1：扩展失败测试，验证占位路由元数据完整**

在 `businessRoutes.spec.ts` 增加：

```ts
it('provides display metadata for every placeholder module', () => {
  for (const route of BUSINESS_ROUTES.filter(item => !item.implemented)) {
    expect(route.title.trim()).not.toBe('')
    expect(route.source.trim()).not.toBe('')
    expect(route.owner.trim()).not.toBe('')
  }
})
```

- [ ] **步骤 2：运行测试确认当前行为**

运行：

```powershell
npm test -- src/router/__tests__/businessRoutes.spec.ts
```

预期：PASS。该测试锁定占位页面所依赖的数据契约，再开始组件实现。

- [ ] **步骤 3：创建统一占位组件**

`ComingSoonView.vue` 使用路由 `meta`，不请求后端：

```vue
<template>
  <main class="coming-soon">
    <section class="coming-soon__card">
      <el-tag type="warning" effect="light">迁移中</el-tag>
      <h1>{{ title }}</h1>
      <p>该模块正在从桌面客户端迁移到 Web。</p>
      <dl>
        <div><dt>原始入口</dt><dd>{{ source }}</dd></div>
        <div><dt>负责模块</dt><dd>{{ owner }}</dd></div>
      </dl>
      <div class="coming-soon__actions">
        <el-button @click="router.go(0)">刷新页面</el-button>
        <el-button type="primary" @click="router.push('/orders')">返回订单总表</el-button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const title = computed(() => String(route.meta.title || '功能开发中'))
const source = computed(() => String(route.meta.source || '桌面客户端'))
const owner = computed(() => String(route.meta.owner || '业务模块'))
</script>
```

样式要求：占满内容区、卡片最大宽度 680px、Element Plus 中性色，不引入图片和新依赖。

- [ ] **步骤 4：注册真实页面和占位页面**

调整 `router/index.ts`：

```ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { BUSINESS_ROUTES } from './businessRoutes'

const implementedRoutes: RouteRecordRaw[] = [
  { path: '/orders', name: 'OrderSummary', component: () => import('@/views/order/OrderSummary.vue') },
  { path: '/orders/:id', name: 'OrderSummaryDetail', component: () => import('@/views/order/OrderSummary.vue') },
  { path: '/orders/:id/import', name: 'OrderImport', component: () => import('@/views/order/OrderImport.vue') },
  { path: '/shipments', name: 'Shipments', component: () => import('@/views/shipment/ShipmentsPage.vue') },
  { path: '/payments', redirect: '/payments/customer' },
  { path: '/payments/customer', name: 'CustomerPayments', component: () => import('@/views/payment/PaymentListPage.vue') },
]

const placeholderRoutes: RouteRecordRaw[] = BUSINESS_ROUTES
  .filter(item => !item.implemented)
  .map(item => ({
    path: item.path,
    name: `ComingSoon-${item.key}`,
    component: () => import('@/views/misc/ComingSoonView.vue'),
    meta: { title: item.title, source: item.source, owner: item.owner },
  }))
```

兜底路由必须使用独立名称：

```ts
{ path: '/:pathMatch(.*)*', name: 'ComingSoonFallback', component: () => import('@/views/misc/ComingSoonView.vue') }
```

- [ ] **步骤 5：运行前端测试与构建**

运行：

```powershell
npm test -- src/router/__tests__/businessRoutes.spec.ts
npm run build
```

预期：路由测试全部通过；`vue-tsc` 和 Vite 构建退出码均为 0。

---

### 任务 3：增强 WebContainerView 导航契约

**文件：**
- 修改：`client/web_container/web_view.py`
- 创建：`tests/client/test_web_tab_routes.py`

- [ ] **步骤 1：编写不依赖 Qt GUI 的 URL 拼接失败测试**

在 `web_view.py` 先计划暴露纯函数 `build_web_url`，测试如下：

```py
from client.web_container.web_view import build_web_url


def test_build_web_url_joins_base_and_route():
    assert build_web_url("https://example.com/", "/products") == "https://example.com/products"


def test_build_web_url_keeps_query_string():
    assert build_web_url("https://example.com", "/orders?pi_no=PI001") == "https://example.com/orders?pi_no=PI001"


def test_build_web_url_rejects_external_route():
    try:
        build_web_url("https://example.com", "https://evil.example")
    except ValueError as exc:
        assert "站内路径" in str(exc)
    else:
        raise AssertionError("应拒绝外部 URL")
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
py -m pytest tests/client/test_web_tab_routes.py -q
```

预期：FAIL，提示无法导入 `build_web_url`。

- [ ] **步骤 3：实现纯 URL 构造函数并复用**

在 `client/web_container/web_view.py` 添加：

```py
def build_web_url(remote_url: str, path: str) -> str:
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Web 容器只允许站内路径')
    return f"{remote_url.rstrip('/')}{path}"
```

修改：

```py
def navigate_to(self, path: str):
    self.load(QUrl(build_web_url(self.remote_url, path)))


def reload_current(self):
    self.reload()
```

- [ ] **步骤 4：运行测试并确认通过**

运行：

```powershell
py -m pytest tests/client/test_web_tab_routes.py -q
```

预期：3 个测试通过。

- [ ] **步骤 5：运行 Python 语法检查**

运行：

```powershell
py -m py_compile client/web_container/web_view.py
```

预期：退出码 0，无输出。

---

### 任务 4：将 PyQt 主窗口切换为单一浏览器容器

**文件：**
- 修改：`client/main.py:72-78`
- 修改：`client/main.py:1794-1808`
- 修改：`client/main.py:1885-1923`
- 修改：`tests/client/test_web_tab_routes.py`

- [ ] **步骤 1：扩展失败测试，锁定客户端路由映射**

避免在测试中导入巨大的 `main.py`，将路由映射定义在 `client/web_container/routes.py`（本任务新增）并由 `main.py` 导入：

```py
from client.web_container.routes import TAB_ROUTES


def test_tab_routes_cover_main_menu():
    assert list(TAB_ROUTES) == [
        'products', 'customers', 'suppliers', 'quotes', 'pi', 'purchase',
        'shipment', 'customer_payment', 'supplier_payment', 'inventory',
        'order_summary', 'web_order',
    ]


def test_tab_routes_use_final_server_paths():
    assert TAB_ROUTES['products'] == '/products'
    assert TAB_ROUTES['shipment'] == '/shipments'
    assert TAB_ROUTES['customer_payment'] == '/payments/customer'
    assert TAB_ROUTES['order_summary'] == '/orders'
    assert TAB_ROUTES['web_order'] == '/orders'
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
py -m pytest tests/client/test_web_tab_routes.py -q
```

预期：FAIL，提示找不到 `client.web_container.routes`。

- [ ] **步骤 3：创建稳定客户端路由映射**

创建 `client/web_container/routes.py`：

```py
TAB_ROUTES = {
    'products': '/products',
    'customers': '/customers',
    'suppliers': '/suppliers',
    'quotes': '/quotes',
    'pi': '/pi',
    'purchase': '/purchases',
    'shipment': '/shipments',
    'customer_payment': '/payments/customer',
    'supplier_payment': '/payments/supplier',
    'inventory': '/inventory',
    'order_summary': '/orders',
    'web_order': '/orders',
}
```

- [ ] **步骤 4：主窗口只创建单个 WebContainerView**

在 `main.py` 导入 `TAB_ROUTES`，将 `QStackedWidget` 与 12 个页面创建替换为：

```py
self.web_content = self._create_web_content()
content_layout.addWidget(self.web_content)
self._web_view.navigate_to(TAB_ROUTES['products'])
```

新增：

```py
def _create_web_content(self):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    if HAS_WEB_CONTAINER:
        from config.local_settings_manager import get_frontend_url
        self._web_view = WebContainerView(get_frontend_url(), self)
        layout.addWidget(self._web_view)
    else:
        self._web_view = None
        hint = QLabel('Web 容器模块不可用（缺少 PySide6 QtWebEngine 组件）')
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
    return widget
```

`switch_tab` 最小实现：

```py
def switch_tab(self, key):
    path = TAB_ROUTES.get(key)
    if path and self._web_view is not None:
        self._web_view.navigate_to(path)
    for name, button in self.tab_buttons.items():
        button.setChecked(name == key)
```

删除 `switch_tab` 内旧 `refresh_map` 调用，避免页面切换继续触发 PyQt API 请求。保留旧 `create_*_tab` 和 `load_*` 方法定义但不再实例化或调用。

- [ ] **步骤 5：处理重复“订单总表 / Web 订单”入口**

本轮保持两个菜单键和相同路径，以兼容用户习惯；在按钮名称上将 `Web 订单` 改为 `订单总表（Web）`，并在后续版本确认无引用后再删除重复入口。本轮不删除 key。

- [ ] **步骤 6：运行客户端测试与语法检查**

运行：

```powershell
py -m pytest tests/client/test_web_tab_routes.py -q
py -m py_compile client/main.py client/web_container/routes.py client/web_container/web_view.py
```

预期：5 个路由/URL 测试通过；Python 编译退出码 0。

---

### 任务 5：全量验证与手动验收

**文件：**
- 验证：`frontend/src/router/index.ts`
- 验证：`client/main.py`
- 验证：`client/web_container/web_view.py`

- [ ] **步骤 1：运行前端全量测试**

运行：

```powershell
npm test
```

工作目录：`frontend-repo/frontend`

预期：所有 Vitest 测试文件通过，0 个失败。

- [ ] **步骤 2：运行前端生产构建**

运行：

```powershell
npm run build
```

工作目录：`frontend-repo/frontend`

预期：`vue-tsc` 与 Vite 均成功，退出码 0；chunk size 警告不视为失败。

- [ ] **步骤 3：运行客户端测试与语法检查**

运行：

```powershell
py -m pytest tests/client -q
py -m py_compile client/main.py client/web_container/routes.py client/web_container/web_view.py
```

工作目录：`pyqt-to-web-migration`

预期：客户端测试全部通过；编译退出码 0。

- [ ] **步骤 4：本地启动前后端**

```powershell
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
npm run dev -- --host 0.0.0.0
```

分别在 `frontend-repo/backend` 和 `frontend-repo/frontend` 运行。预期后端监听 `8000`，前端监听 `5173`。

- [ ] **步骤 5：手动验收 12 个菜单**

逐项点击并记录路径：

```text
产品管理          /products              占位页
客户管理          /customers             占位页
供应商管理        /suppliers             占位页
报价管理          /quotes                占位页
PI管理            /pi                    占位页
采购管理          /purchases             占位页
出货管理          /shipments             真实页
客户付款          /payments/customer     真实页
供应商付款        /payments/supplier     占位页
库存管理          /inventory             占位页
订单总表          /orders                真实页
订单总表（Web）   /orders                真实页
```

验收要求：同一浏览器实例内切换；按钮选中状态正确；无旧 PyQt API 刷新日志；浏览器后退/前进可工作。

- [ ] **步骤 6：验证无需更新客户端的服务器替换流程**

临时把 `/products` 的路由组件从 `ComingSoonView` 替换为一个测试组件，重建并刷新 PyQt 页面。预期客户端代码与 `TAB_ROUTES` 均不变，刷新后展示测试组件。验证后恢复占位路由。

- [ ] **步骤 7：检查最终差异**

```powershell
git diff --check
git status --short
```

分别在 `frontend-repo` 和实际包含 `pyqt-to-web-migration` 的 Git 仓库根目录运行。预期无空白错误；只出现计划内文件。不要提交或推送，除非用户明确要求。

---

## 规格覆盖自检

- 单一 `WebContainerView`：任务 4。
- 12 个稳定业务路由：任务 1、任务 4。
- 已实现页面直接使用、未实现页面统一占位：任务 2。
- 服务器发布后无需客户端升级：任务 1 的最终路径契约 + 任务 5 步骤 6。
- 路由错误兜底：任务 2。
- URL 拼接与外部跳转防护：任务 3。
- 不删除旧 PyQt 业务实现、可回退：任务 4 明确保留定义。
- 自动测试、构建、客户端语法和手工验收：任务 5。

## 实施约束

- 不新增占位后端接口；静态占位元数据足够完成当前需求，避免无业务价值的 API。
- 不删除旧 PyQt 页面代码，只停止创建和刷新，防止一次性迁移造成不可逆回退风险。
- 不把前端页面实现状态写入客户端；客户端只知道路径。
- 不在本计划中迁移产品、客户、供应商等具体业务功能。
