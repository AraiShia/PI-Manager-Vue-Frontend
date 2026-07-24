# Qt QWebChannel 离线部署实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 完成 M1-M4 全量实现，使 PyInstaller 打包的 exe 可作为纯离线启动器，通过 QWebChannel + file:// 加载本地前端，通过 CDN 下载热更新；前端支持三态通信模式（local-offline / local-online / remote-web）。

**架构：** PySide6/PyQt5 双导入，exe 不启动 HTTP 服务。离线模式通过 QWebChannel RPC 调用 SQLite CRUD，在线模式通过 axios → 远程 API。

**技术栈：** PySide6/PyQt5, SQLAlchemy, PyInstaller, QWebChannel, ECDSA 签名校验, SHA-256, Axios 自定义 Adapter

---

## 文件变更清单

### 新增文件
- `backend/tests/test_offline_features.py` — 离线功能测试（已有占位）
- `frontend/src/utils/modeDetector.ts` — 三态检测器（已完成）

### 修改文件
- `backend/qt_bridge.py` — 修复 supplier.create dept_id，补充 productSupplierUrls 方法
- `backend/run_qt.py` — 集成 CDN 更新检查，修复 exec/exec_ 双导入
- `backend/frontend_manager.py` — 集成启动流程调用
- `frontend/src/api/client.ts` — 补充完整 RPC 路由映射
- `frontend/src/api/nativeBridge.ts` — 补充 productSupplierUrls RPC 封装
- `frontend/vite.config.ts` — 确认 legacy 插件配置

---

## 实施里程碑

### M1: 基础框架（纯离线）

#### 任务 1：修复 `supplier.create` dept_id 硬编码

**文件：** 修改 `backend/qt_bridge.py:97`

- [ ] **步骤 1：读取当前代码确认缺陷**

读取 `backend/qt_bridge.py` 第 97 行附近代码：
```python
# 2. 新增供应商
elif method == "suppliers.create":
    payload = SupplierCreate(**params)
    db_supplier = create_supplier(db, payload, dept_id="S")  # ← 硬编码
```

- [ ] **步骤 2：修复 dept_id 从 params 获取**

将 `dept_id="S"` 改为从 `params.get("dept_id", "S")` 获取，兼容无 dept_id 参数的旧调用：

```python
elif method == "suppliers.create":
    payload = SupplierCreate(**params)
    dept_id = params.get("dept_id", "S")
    db_supplier = create_supplier(db, payload, dept_id=dept_id)
```

- [ ] **步骤 3：Commit**

```bash
git add backend/qt_bridge.py
git commit -m "fix(qt): supplier.create 从 params 获取 dept_id，移除硬编码 S"
```

---

#### 任务 2：修复 `run_qt.py` exec/exec_ 双导入

**文件：** 修改 `backend/run_qt.py:90`

- [ ] **步骤 1：读取当前代码**

读取 `backend/run_qt.py` 第 90 行：
```python
sys.exit(app.exec_())  # ← PyQt5 用 exec_()，PySide6 用 exec()
```

- [ ] **步骤 2：统一为兼容写法**

```python
# PySide6 用 exec()，PyQt5 用 exec_()；hasattr 兼容两者
if hasattr(app, 'exec'):
    sys.exit(app.exec())
else:
    sys.exit(app.exec_())
```

或更简洁的 hasattr 判断：
```python
sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())
```

- [ ] **步骤 3：Commit**

```bash
git add backend/run_qt.py
git commit -m "fix(qt): run_qt.py 兼容 PySide6 exec() / PyQt5 exec_()"
```

---

#### 任务 3：集成 CDN 更新检查到启动流程

**文件：** 修改 `backend/run_qt.py` + `backend/frontend_manager.py`

- [ ] **步骤 1：读取 frontend_manager.py 中的 `update_frontend` 调用方式**

```bash
grep -n "update_frontend\|check_update\|version.json" backend/frontend_manager.py
```

- [ ] **步骤 2：在 `run_qt.py` 中，在加载前端之前插入异步更新检查**

在 `frontend_manager.ensure_baseline_frontend()` 之后、`view.setUrl()` 之前插入：

```python
# 异步检查 CDN 更新（不阻塞 UI 展示）
import threading

def _async_check_update(fm: FrontendManager):
    try:
        # 联网检测（3s 超时）
        import urllib.request
        try:
            r = urllib.request.urlopen(
                "https://cdn.example.com/pi-manager/version.json", timeout=3
            )
            manifest = json.loads(r.read().decode())
            # ECDSA 签名验证在 FrontendManager.update_frontend 内部
            if fm.verify_manifest_signature(manifest):
                if fm.update_frontend(manifest):
                    # 有更新时通过 Bridge 通知前端
                    bridge.emit_version_available(manifest.get("version", ""))
        except Exception:
            pass  # 联网失败静默忽略，不阻断启动

threading.Thread(target=_async_check_update, args=(frontend_manager,), daemon=True).start()
```

- [ ] **步骤 3：Commit**

```bash
git add backend/run_qt.py
git commit -m "feat(qt): run_qt.py 集成异步 CDN 更新检查，不阻塞 UI"
```

---

### M2: 前端更新机制

#### 任务 4：前端更新提示 UI 集成

**文件：** 修改 `frontend/src/App.vue`（或 `NativeBridge.vue`）

- [ ] **步骤 1：读取 `NativeBridge.vue` 了解当前初始化时机**

```bash
cat frontend/src/components/NativeBridge.vue
```

- [ ] **步骤 2：在 App.vue 的 onMounted 中监听 `bridge.onVersionAvailable` 信号**

```typescript
import { getBridge } from '@/api/nativeBridge'
import { ElMessageBox } from 'element-plus'

const bridge = getBridge()
if (bridge) {
  bridge.onVersionAvailable((version: string) => {
    ElMessageBox.confirm(
      `发现新版本 ${version}，是否刷新页面？`,
      '前端更新就绪',
      {
        confirmButtonText: '刷新页面',
        cancelButtonText: '稍后',
        type: 'info',
      }
    ).then(() => {
      bridge.triggerRefresh().then(() => {
        window.location.reload()
      })
    }).catch(() => {
      // 用户取消，下次启动自动加载新版本
    })
  })
}
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat(前端): App.vue 监听 onVersionAvailable 信号，提示用户刷新"
```

---

### M3: 扩展 QWebChannel RPC 覆盖

#### 任务 5：补充 `productSupplierUrls` RPC 方法

**文件：** 修改 `backend/qt_bridge.py`

- [ ] **步骤 1：在 `qt_bridge.py` 中新增 productSupplierUrls 分发分支**

在 `call()` 方法的 `except Exception` 块之前、`else` 分支之后，添加：

```python
# 8. 产品-供应商-URL 列表
elif method == "productSupplierUrls.list":
    from crud.product_supplier_url import list_urls
    skip_p = params.get("skip", 0)
    limit_p = params.get("limit", 20)
    # params 支持 product_id / supplier_id / supplier_name 组合查询
    product_id = params.get("product_id")
    supplier_id = params.get("supplier_id")
    supplier_name = params.get("supplier_name")
    if not product_id:
        return json.dumps({
            "success": False,
            "data": None,
            "error": "product_id 为必填参数"
        }, ensure_ascii=False)
    urls = list_urls(
        db,
        product_id=int(product_id),
        supplier_id=int(supplier_id) if supplier_id else None,
        supplier_name=supplier_name,
    )
    return json.dumps({
        "success": True,
        "data": [{"id": u.id, "product_id": u.product_id,
                  "supplier_id": u.supplier_id, "supplier_name": u.supplier_name,
                  "url": u.url, "display_name": u.display_name,
                  "is_default": u.is_default,
                  "created_at": str(u.created_at) if u.created_at else None}
                 for u in urls],
        "error": None
    }, ensure_ascii=False)

# 9. 产品-供应商-URL 新增
elif method == "productSupplierUrls.create":
    from schemas.product_supplier_url import ProductSupplierUrlCreate
    from crud.product_supplier_url import create_url
    payload = ProductSupplierUrlCreate(**params)
    url_obj, created = create_url(db, payload)
    db.commit()
    data = {
        "id": url_obj.id,
        "product_id": url_obj.product_id,
        "supplier_id": url_obj.supplier_id,
        "supplier_name": url_obj.supplier_name,
        "url": url_obj.url,
        "display_name": url_obj.display_name,
        "is_default": url_obj.is_default,
        "created_at": str(url_obj.created_at) if url_obj.created_at else None,
    }
    return json.dumps({
        "success": True,
        "data": data,
        "error": None,
        "created": created
    }, ensure_ascii=False)
```

- [ ] **步骤 2：补充前端 `nativeBridge.ts` RPC 封装**

在 `frontend/src/api/nativeBridge.ts` 末尾添加：

```typescript
// productSupplierUrls RPC 封装
export async function listSupplierUrls(params: {
  product_id: number
  supplier_id?: number
  supplier_name?: string
}): Promise<ProductSupplierUrl[]> {
  const result = await call('productSupplierUrls.list', params)
  return result as ProductSupplierUrl[]
}

export async function createSupplierUrl(params: {
  product_id: number
  supplier_id: number
  supplier_name: string
  url: string
  display_name?: string
  is_default?: boolean
}): Promise<{ id: number; created: boolean }> {
  return await call('productSupplierUrls.create', params) as any
}
```

- [ ] **步骤 3：Commit**

```bash
git add backend/qt_bridge.py frontend/src/api/nativeBridge.ts
git commit -m "feat(qt): 补充 productSupplierUrls.list 和 create RPC 方法"
```

---

#### 任务 6：补充更多核心 RPC 方法（pi / purchase / customer）

**文件：** 修改 `backend/qt_bridge.py`

优先补充使用频率最高的 3 个模块方法：

- `pi.list` — PI 列表
- `purchase.createOnline` — 1688 线上采购创建
- `customer.list` — 客户列表

- [ ] **步骤 1：补充 pi.list RPC**

```python
# 10. PI 列表
elif method == "pi.list":
    from crud.pi import list_pi
    dept_id = params.get("dept_id", "S")
    skip_p = params.get("skip", 0)
    limit_p = params.get("limit", 20)
    status = params.get("status")
    records = list_pi(db, skip=skip_p, limit=limit_p, status=status, dept_id=dept_id)
    return json.dumps({
        "success": True,
        "data": records,
        "error": None
    }, ensure_ascii=False)
```

- [ ] **步骤 2：补充前端 client.ts 路由映射**

在 `frontend/src/api/client.ts` 的 `matchRpcRoute` 映射表中添加：

```typescript
{ url: 'api/pi', method: 'GET', rpcMethod: 'pi.list' },
{ url: 'api/purchase-orders', method: 'POST', rpcMethod: 'purchase.createOnline' },
{ url: 'api/customers', method: 'GET', rpcMethod: 'customer.list' },
```

- [ ] **步骤 3：Commit**

```bash
git add backend/qt_bridge.py frontend/src/api/client.ts
git commit -m "feat(qt): 补充 pi.list / purchase.createOnline / customer.list RPC"
```

---

### M4: 降级与异常处理

#### 任务 7：`local-online` 模式实现（三态完整）

**文件：** 修改 `frontend/src/api/client.ts` + `frontend/src/utils/modeDetector.ts`

- [ ] **步骤 1：确认 modeDetector.ts 当前实现**

读取 `frontend/src/utils/modeDetector.ts`：
- 当前返回 `'local-offline' | 'local-online' | 'remote-web'`
- `local-online` 定义为 `forceOffline || !navigator.onLine ? 'local-offline' : 'local-online'`

- [ ] **步骤 2：修改 client.ts 中 local-online 的 adapter 逻辑**

当前 `qwebchannelAdapter` 只处理 `local-offline`。修改：

```typescript
const qwebchannelAdapter = async (config: any): Promise<any> => {
  // local-online: QWebChannel RPC 调用，但 CDN 更新检查由 FrontendManager 负责
  const mode = detectAppMode()
  if (mode !== 'local-offline') {
    // local-online 或 remote-web 不走 QWebChannel adapter
    return Promise.reject({ __skip: true })
  }
  // ... 原有 RPC 逻辑
}
```

同时修改 axios 实例的 adapter 逻辑，使 local-online 模式时走 `qwebchannelAdapter`：

```typescript
const axiosInstance = axios.create({
  baseURL: runtimeApiBase(),
  timeout: 30000,
  adapter: async (config) => {
    const mode = detectAppMode()
    if (mode === 'local-offline') {
      const matched = matchRpcRoute(config.url, config.method)
      if (matched) {
        // 调用 QWebChannel
        return qwebchannelAdapter(config)
      }
      // 未配置映射时降级提示
      return Promise.reject({
        message: `离线路由未配置: ${config.method} ${config.url}`,
        config
      })
    }
    if (mode === 'local-online') {
      // local-online 暂不支持，等待后续扩展
      return Promise.reject({ __skip: true })
    }
    // remote-web: 走默认 xhr adapter
    return axios.defaults.adapter!(config)
  }
})
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/api/client.ts frontend/src/utils/modeDetector.ts
git commit -m "feat(前端): client.ts adapter 区分 local-offline / local-online / remote-web 三态"
```

---

#### 任务 8：QWebChannel 初始化失败降级提示

**文件：** 修改 `frontend/src/components/NativeBridge.vue`

- [ ] **步骤 1：读取 NativeBridge.vue**

- [ ] **步骤 2：在 `init()` 失败回调中，检测是否在 file:// 协议下并弹出配置提示**

当前 `init()` 的 catch 分支已有日志，补充 file:// 协议降级：

```typescript
init(): Promise<boolean> {
  // ... 现有逻辑 ...
  } catch (e) {
    if (window.location.protocol === 'file:') {
      const hasLocalConfig = localStorage.getItem('fallback_api_base')
      if (!hasLocalConfig) {
        ElMessageBox.prompt(
          '离线模式无可用桥接，请输入远程 API 地址（或留空使用默认）',
          '配置 API 服务器',
          { inputValue: 'https://piapi.wakabashia.tj.cn' }
        ).then(({ value }) => {
          if (value.trim()) {
            localStorage.setItem('fallback_api_base', value.trim())
          }
          ElMessage.info('已保存，可刷新页面重试')
        }).catch(() => {})
      }
    }
    console.warn('[nativeBridge] 初始化失败:', e)
    return false
  }
}
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/NativeBridge.vue
git commit -m "feat(前端): NativeBridge 初始化失败时引导用户配置 fallback API"
```

---

## 验证清单

### M1 验证
```bash
# 1. 确认 supplier.create dept_id 修复
grep "dept_id" backend/qt_bridge.py | grep "params.get"

# 2. 确认 exec 兼容写法
grep "exec()" backend/run_qt.py

# 3. 确认 CDN 更新线程已集成
grep "threading.Thread" backend/run_qt.py

# 4. npm run build 成功
cd frontend && npm run build
```

### M2 验证
```bash
# 前端构建产物包含 CSP meta 标签
grep -r "Content-Security-Policy" frontend/dist/
```

### M3 验证
```bash
# 确认 productSupplierUrls RPC 分发分支存在
grep "productSupplierUrls" backend/qt_bridge.py

# 确认前端 RPC 封装存在
grep "listSupplierUrls" frontend/src/api/nativeBridge.ts
```

### M4 验证
```bash
# 确认三态分支
grep "local-offline\|local-online\|remote-web" frontend/src/utils/modeDetector.ts
```
