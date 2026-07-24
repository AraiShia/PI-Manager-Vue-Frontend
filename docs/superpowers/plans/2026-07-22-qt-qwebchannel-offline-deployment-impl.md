# Qt QWebChannel 离线部署实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 完成剩余 3 个任务，实现完整的离线客户端功能。

**架构：** PySide6/PyQt5 双导入，exe 不启动 HTTP 服务。离线模式通过 QWebChannel RPC 调用 SQLite CRUD，在线模式通过 axios → 远程 API。

---

## 完成状态概览

| 里程碑 | 任务 | 状态 |
|---------|------|------|
| M1 | 任务 1 supplier.create dept_id 修复 | ✅ 已完成 |
| M1 | 任务 2 exec/exec_ 兼容性 | ✅ 已完成 |
| M1 | 任务 3 CDN 异步更新集成 | ✅ 已完成 |
| M2 | 任务 4 前端更新提示 UI | ❌ **待做** |
| M3 | 任务 5 productSupplierUrls RPC 后端分发 | ❌ **待做** |
| M3 | 任务 6 pi/purchase/customer RPC | ✅ 已完成 |
| M4 | 任务 7 三态 adapter | ✅ 已完成 |
| M4 | 任务 8 QWebChannel 失败降级 | ❌ **待做** |

---

## 剩余任务详情

### M2: 前端更新机制

#### 任务 4：前端更新提示 UI 集成

**文件：** 修改 `frontend/src/App.vue`

**当前状态：** `NativeBridge.vue` 初始化时未监听 `bridge.version_available` 信号，`App.vue` 也未监听。

- [ ] **步骤 1：读取 NativeBridge.vue 和 App.vue**

确认当前初始化时机和文件结构：
```bash
cat frontend/src/components/NativeBridge.vue
cat frontend/src/App.vue | grep -n "onMounted\|onVersionAvailable\|nativeBridge"
```

- [ ] **步骤 2：在 App.vue 的 onMounted 中监听 `bridge.onVersionAvailable` 信号**

在 `onMounted` 中：

```typescript
import { getBridge } from '@/api/nativeBridge'
import { ElMessageBox } from 'element-plus'

onMounted(async () => {
  // 监听 PyQt5 发出的新版本可用信号
  const bridge = getBridge()
  if (bridge && typeof bridge.versionAvailable !== 'undefined') {
    bridge.versionAvailable.connect((version: string) => {
      ElMessageBox.confirm(
        `发现新版本 ${version}，是否刷新页面以加载最新功能？`,
        '前端更新就绪',
        {
          confirmButtonText: '刷新页面',
          cancelButtonText: '下次再说',
          type: 'info',
        }
      ).then(() => {
        window.location.reload()
      }).catch(() => {
        // 用户取消，下次启动自动加载新版本
      })
    })
  }
})
```

注意：`bridge.versionAvailable` 是 PySide6 Signal，在 TS 中使用 `.connect()` 方法订阅。如果 TS 类型未定义，可用 `(bridge as any).versionAvailable.connect(...)` 绕过。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat(前端): App.vue 监听 bridge.versionAvailable 信号，提示用户刷新"
```

---

### M3: 扩展 QWebChannel RPC 覆盖

#### 任务 5：补充 `productSupplierUrls` RPC 后端分发

**文件：** 修改 `backend/qt_bridge.py`

**当前状态：** `qt_bridge.py` 中只有 7 个 supplier 方法，尚无 productSupplierUrls 分发。前端 `client.ts` 也无映射。

- [ ] **步骤 1：在 `qt_bridge.py` 的 `call()` 方法末尾（`else` 分支之前）添加分发分支**

在 `elif method == "suppliers.delete": ... else:` 之间插入：

```python
    # 8. 产品-供应商-URL 列表
    elif method == "productSupplierUrls.list":
        from crud.product_supplier_url import list_urls as crud_list_urls
        product_id = params.get("product_id")
        if not product_id:
            return json.dumps({
                "success": False,
                "data": None,
                "error": "product_id 为必填参数"
            }, ensure_ascii=False)
        supplier_id = params.get("supplier_id")
        supplier_name = params.get("supplier_name")
        urls = crud_list_urls(
            db,
            product_id=int(product_id),
            supplier_id=int(supplier_id) if supplier_id else None,
            supplier_name=supplier_name,
        )
        return json.dumps({
            "success": True,
            "data": [{
                "id": u.id,
                "product_id": u.product_id,
                "supplier_id": u.supplier_id,
                "supplier_name": u.supplier_name,
                "url": u.url,
                "display_name": u.display_name,
                "is_default": u.is_default,
                "created_at": str(u.created_at) if u.created_at else None,
            } for u in urls],
            "error": None
        }, ensure_ascii=False)

    # 9. 产品-供应商-URL 新增
    elif method == "productSupplierUrls.create":
        from crud.product_supplier_url import create_url as crud_create_url
        from schemas.product_supplier_url import ProductSupplierUrlCreate
        try:
            payload = ProductSupplierUrlCreate(**params)
        except Exception as e:
            return json.dumps({
                "success": False,
                "data": None,
                "error": f"参数错误: {str(e)}"
            }, ensure_ascii=False)
        url_obj, created = crud_create_url(db, payload)
        db.commit()
        return json.dumps({
            "success": True,
            "data": {
                "id": url_obj.id,
                "product_id": url_obj.product_id,
                "supplier_id": url_obj.supplier_id,
                "supplier_name": url_obj.supplier_name,
                "url": url_obj.url,
                "display_name": url_obj.display_name,
                "is_default": url_obj.is_default,
                "created_at": str(url_obj.created_at) if url_obj.created_at else None,
            },
            "created": created,
            "error": None
        }, ensure_ascii=False)
```

- [ ] **步骤 2：补充前端 `client.ts` 路由映射**

在 `matchRpcRoute` 函数末尾（`return null` 之前）添加：

```typescript
  // 11. GET /api/product-supplier-urls -> URL 列表
  const psuListMatch = cleanUrl.match(/^api\/product-supplier-urls$/)
  if (psuListMatch && methodUpper === 'GET') {
    return {
      rpcMethod: 'productSupplierUrls.list',
      mapParams: (config: any) => config.params || {}
    }
  }

  // 12. POST /api/product-supplier-urls -> 新增 URL
  if (cleanUrl === 'api/product-supplier-urls' && methodUpper === 'POST') {
    return {
      rpcMethod: 'productSupplierUrls.create',
      mapParams: (config: any) => config.data || {}
    }
  }
```

- [ ] **步骤 3：Commit**

```bash
git add backend/qt_bridge.py frontend/src/api/client.ts
git commit -m "feat(qt): 补充 productSupplierUrls.list 和 create RPC 后端分发与前端映射"
```

---

### M4: 降级与异常处理

#### 任务 8：QWebChannel 初始化失败降级提示

**文件：** 修改 `frontend/src/components/NativeBridge.vue`

**当前状态：** `nativeBridge.init()` 的 catch 分支只打 console.warn，无 file:// 协议降级提示。

- [ ] **步骤 1：读取 NativeBridge.vue 当前 init() 实现**

确认 catch 分支的当前代码：
```bash
grep -n "catch\|file:\|ElMessageBox\|fallback" frontend/src/components/NativeBridge.vue
```

- [ ] **步骤 2：在 NativeBridge.vue 的 catch 分支中补充 file:// 降级弹框**

在 `NativeBridge.vue` 的 `<script setup>` 中找到 `init()` 的 catch 块：

```typescript
// 查找当前 catch 块位置
cat frontend/src/components/NativeBridge.vue | grep -n "catch"
```

如果当前 `nativeBridge.init()` 调用在 `NativeBridge.vue` 中，且 catch 只打日志，补充：

```typescript
} catch (e) {
  if (window.location.protocol === 'file:') {
    // file:// 协议下无可用桥接，引导用户配置远程 API
    const saved = localStorage.getItem('fallback_api_base')
    if (!saved) {
      ElMessageBox.prompt(
        '离线模式无可用桥接，请输入远程 API 地址',
        '配置 API 服务器',
        { inputValue: 'https://piapi.wakabashia.tj.cn' }
      ).then(({ value }) => {
        if (value?.trim()) {
          localStorage.setItem('fallback_api_base', value.trim())
          ElMessage.info('已保存，请刷新页面')
        }
      }).catch(() => {})
    }
  }
  console.warn('[NativeBridge] Running in browser mode:', e)
}
```

如果 `NativeBridge.vue` 中 `nativeBridge` 的调用方式是：
```html
<NativeBridge @initialized="onNativeBridgeReady" />
```
则降级逻辑放在 `onNativeBridgeReady(false)` 分支中处理。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/NativeBridge.vue
git commit -m "feat(前端): NativeBridge 初始化失败时引导用户配置 fallback API"
```

---

## 验证清单

```bash
# 任务 4 验证
grep -n "versionAvailable" frontend/src/App.vue
grep -n "ElMessageBox" frontend/src/App.vue

# 任务 5 验证
grep "productSupplierUrls" backend/qt_bridge.py
grep "productSupplierUrls" frontend/src/api/client.ts

# 任务 8 验证
grep -n "fallback_api_base\|ElMessageBox" frontend/src/components/NativeBridge.vue

# 整体验证
cd frontend && npm run build
```
