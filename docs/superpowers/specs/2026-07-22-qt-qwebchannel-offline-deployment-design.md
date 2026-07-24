# Qt QWebChannel 离线部署设计规格

> 目标：将 PI Manager 前端与后端在部署形态上彻底分离。离线时通过 QWebChannel + file:// 加载本地前端，在线时通过 axios 访问远程 API。前端支持 CDN 热更新，exe 作为纯启动器不启动 HTTP 服务。

**修订历史：**
- v1: 初始版本，基于头脑风暴结果

---

## 1. 整体架构

### 1.1 部署形态

```
┌──────────────────────────────────────────────────────────────┐
│                      exe (PyInstaller 打包)                  │
│                                                              │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────┐ │
│  │  Launcher    │  │  FrontendManager   │  │ QWebChannel  │ │
│  │  启动器入口   │  │  前端包下载/管理    │  │  API 暴露    │ │
│  └──────────────┘  └───────────────────┘  └──────────────┘ │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              │ QWebChannel (PyQt5)          │
│                     ┌────────▼──────────────┐               │
│                     │dist-v1.0.0.x/index.h  │(file:// 协议) │
│                     └───────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
         │                              │
         │  CDN / Nginx                 │  axios → remote API
         │  托管 dist.zip               │  (在线模式)
         ▼                              ▼
   前端更新包来源              https://piapi.wakabashia.tj.cn
```

### 1.2 通信模式

| 加载方式 | 通信链路 | 用途 |
|----------|----------|------|
| `file://` 本地加载 | QWebChannel → Python → SQLite | 离线模式，零网络 |
| 远程 CDN 加载（在线） | axios → `https://piapi.wakabashia.tj.cn` | 在线模式，全功能 |

**核心原则：exe 不启动 HTTP 服务。** 无论哪种模式，API 通信都不经过本地 exe。

### 1.3 exe 职责（仅启动器）

- 启动 PyQt5 WebEngine 加载前端页面
- 管理前端包下载、解压、版本目录隔离更新（避免 Windows 文件锁冲突）
- 通过 QWebChannel 向前端暴露基础 API（离线模式使用）
- 检测联网状态、版本更新提示
- **不**监听任何 HTTP 端口

---

## 2. 加载流程

### 2.1 完整启动流程

```
[exe 启动]
    │
    ├── 1. 联网检测（异步，不阻塞 UI）
    │       │
    │       ├── 超时 3s 无响应 → 标记为离线，直接进入步骤 3
    │       │
    │       └── 联网成功 → 检查 CDN 版本
    │               │
    │               ├── 已是最新 → 进入步骤 2
    │               │
    │               └── 发现新版本 →
    │                       ├── 后台下载 dist-v1.0.0.x.zip
    │                       ├── 解压到 AppData/frontend/dist-v1.0.0.x/
    │                       ├── SHA-256 校验完整性
    │                       ├── 写入 config.json: active_version
    │                       └── Toast: "新版本已就绪，点击刷新"
    │
    ├── 2. 选择前端加载路径（依据 config.json 的 active_version）
    │       │
    │       ├── AppData/frontend/dist-{active_version}/index.html 存在？ → 加载它
    │       └── 不存在 → 加载 exe 内置 _MEIPASS/frontend_dist/index.html（兜底）
    │
    └── 3. 启动 WebEngine 并加载
            │
            └── QWebChannel 初始化，暴露 API 对象到 window.pywebview.api
```

### 2.2 前端加载路径优先级

```
优先级高
  1. AppData/frontend/dist-v{active_version}/  ← CDN 下载的最新版本（可热更）
  2. _MEIPASS/frontend_dist/                   ← exe 内置兜底包（永不更新）
优先级低
```

---

## 3. QWebChannel API 设计

### 3.1 Python 端暴露接口

位置：`backend/` 新建 `qt_bridge.py`，由 exe 入口加载。

```python
# qt_bridge.py
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

class QtBridge(QObject):
    # 信号：通知前端事件
    version_available = pyqtSignal(str)  # 新版本可用
    network_status_changed = pyqtSignal(bool)  # 联网状态变更

    @pyqtSlot(result=str)
    def get_app_version(self):
        """返回当前 exe 版本"""
        return self._version

    @pyqtSlot(str, result=str)
    def get_db_version(self):
        """返回 SQLite schema 版本"""
        return self._get_schema_version()

    @pyqtSlot(result=str)
    def get_network_status(self):
        """返回联网状态：'online' | 'offline'"""
        return 'online' if self._check_network() else 'offline'

    @pyqtSlot(result=str)
    def get_frontend_version(self):
        """返回当前加载的前端版本号（来自 index.html 同目录 version.json）"""
        ...

    @pyqtSlot(result=str)
    def check_update(self):
        """主动检查更新，返回 'latest' | 新版本号"""
        ...

    @pyqtSlot(result=str)
    def trigger_refresh(self):
        """强制刷新页面加载最新 dist"""
        self._reload_browser()
        return 'ok'

    # --- 业务数据接口（离线模式使用）---

    @pyqtSlot(int, int, int, result=str)
    def list_suppliers(self, skip, limit, dept_id):
        """查询供应商列表（JSON 字符串）"""
        ...

    @pyqtSlot(int, result=str)
    def get_supplier(self, supplier_id):
        ...

    @pyqtSlot(str, result=str)
    def create_or_get_supplier(self, payload_json):
        """find-or-create 供应商"""
        ...
```

### 3.2 前端调用方式

```typescript
// src/api/nativeBridge.ts 已有封装，扩展支持所有业务接口
import { initQWebChannel, callQtApi } from '@/api/nativeBridge'

// 离线模式调用示例
const suppliers = await callQtApi('list_suppliers', [0, 20, deptId])
const parsed = JSON.parse(suppliers)

// 在线模式仍使用 axios
const suppliersOnline = await suppliersApi.list({ skip: 0, limit: 20 })
```

### 3.3 通信模式自动切换

```typescript
// src/api/base.ts 扩展
function getApiBase(): string {
  // file:// 协议加载 → 使用 QWebChannel（本地桥接）
  if (window.location.protocol === 'file:') {
    return 'qwebchannel://'
  }
  // HTTPS 页面自动使用同源
  if (window.location.protocol === 'https:') {
    return window.location.origin
  }
  // HTTP 页面使用配置地址
  return import.meta.env.VITE_API_BASE_URL || ''
}
```

所有业务 API 调用通过统一封装，根据加载来源自动选择 QWebChannel 或 axios。

---

## 4. 前端更新机制

### 4.1 版本检测

CDN 服务器上放置 `version.json`：

```json
{
  "version": "1.0.0.35",
  "dist_url": "https://cdn.example.com/pi-manager/dist-v1.0.0.35.zip",
  "sha256": "a3f5c8d9e1b2...",
  "min_app_version": "1.0.0.28"
}
```

exe 启动时请求此文件，对比 `min_app_version` 与当前 exe 版本，决定是否下载。

### 4.2 基于版本目录的更新流程 (规避 Windows 文件独占锁)

由于 Windows 操作系统中，若 PyQt5 WebEngine 占用了正在运行的静态资源文件，直接对运行中的 `dist` 目录进行覆盖或重命名会导致 `PermissionError: [WinError 5] 拒绝访问`。因此采用基于版本号子目录的隔离更新流程：

```
下载 dist-v1.0.0.35.zip → 临时解压目录
    │
    ├── 解压到 AppData/frontend/dist-v1.0.0.35/ (全新独立目录)
    ├── SHA-256 校验，确认解压内容完整
    ├── 修改本地配置文件 config.json: active_version = "1.0.0.35"
    │
    └── 前端提示刷新
            │
            ├── 用户点击刷新 → window.location.reload() (WebEngine 重新加载 active_version 指定的新路径)
            │
            └── 用户忽略 → 下次启动自动加载新版本目录
```

### 4.3 回滚与清理机制

```
启动或刷新时检测当前 active_version 对应的 index.html 是否存在
    │
    ├── 损坏或丢失 → 遍历 AppData/frontend/ 下所有 dist-v*/ 目录
    │       ├── 找到可用的最新版本 → 更新 config.json 的 active_version → 加载它
    │       └── 均不可用 → 加载 _MEIPASS 内置的 frontend_dist/ 目录
    │
    └── 定期清理：启动成功后，异步删除除当前 active_version 外、超过 3 个版本以上的历史 dist-v* 目录，避免占用过多磁盘空间
```

---

## 5. 错误处理与安全降级

### 5.1 降级链路

| 场景 | 降级路径 |
|------|----------|
| CDN 下载失败 | 使用本地最新已下载的 `dist-v*` 版本或内置兜底 |
| SHA-256 校验失败 | 清理已下载的临时目录，保留当前 `active_version` |
| 当前版本 `index.html` 损坏 | 扫描本地其他 `dist-v*` 目录回滚，或加载内置兜底 |
| QWebChannel 初始化失败 | 前端降级到纯 Web 模式（需配置远程 API 地址） |
| Python 端 DB 操作失败 | 通过 QWebChannel error 信号通知前端，弹窗提示 |

> 注：原 §2.1 早期提到的"dist/ → dist_bak/"两目录互斥方案已被 §4.2 的"版本目录隔离"方案取代，避免 Windows 平台 PyQt5 WebEngine 文件独占锁导致的 `PermissionError`。

### 5.2 前端降级模式

当 `file://` 加载但 QWebChannel 不可用时，前端弹出配置框让用户输入远程 API 地址：

```typescript
// 检测降级逻辑，在 file 协议且无 Bridge 时引导用户手动配置 API
if (window.location.protocol === 'file:') {
  const hasQtBridge = !!(window as any).pywebview
  if (!hasQtBridge) {
    ElMessageBox.prompt('请输入 API 服务器地址', '离线模式无可用桥接', {
      inputValue: 'https://piapi.wakabashia.tj.cn',
    }).then(({ value }) => {
      // 降级保存本地 fallback API 配置以供后续 axios 访问使用
      localStorage.setItem('fallback_api_base', value)
    })
  }
}
```

### 5.3 安全配置与跨域 (CORS) 处理

#### 1. PyQt5 允许本地 file 协议跨域访问远程 API
当在线模式下前端通过 `file://` 加载时，访问远程 API 域名会触发 CORS 限制（由于 Origin 为 `null`）。必须在 PyQt5 启动时放开限制：
```python
# PyQt5 启动配置，放开本地 content 对远程 API URL 的访问限制
settings = QWebEngineSettings.globalSettings()
settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
```

#### 2. 安全沙箱与 API 防护
- **Bridge 最小化暴露：** `QtBridge` 绝对不要暴露任何操作系统执行 shell 的通用 slot 方法，只允许暴露经过参数类型校验的 SQLite 数据读写 slot。
- **输入合法性过滤：** Python 侧所有 `@pyqtSlot` 方法在接收到前端参数后，必须进行严格的数据格式校验与 SQL 注入过滤。
- **内容安全策略 (CSP)：** 在前端的 `index.html` 中注入严格的 Content Security Policy，只允许加载本地打包的 JS 资源，防范 XSS 劫持：
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self' file: https:; script-src 'self' 'unsafe-inline' file:; style-src 'self' 'unsafe-inline' file:;">
```

---

## 6. 数据库迁移

### 6.1 离线模式的数据库操作

离线模式下，前端通过 QWebChannel 调用 Python 方法操作 SQLite。数据库文件路径：

```
%APPDATA%\PIManager\data\pimain.db
```

> 注：`PIManager` 是当前 PyInstaller 打包产物的应用目录名（`PI-Manager-Server.exe` 对应 `PIManager`）。如有调整需同步修改此路径。

### 6.2 Schema 版本管理

```python
# qt_bridge.py
MIGRATIONS = [
    ('1.0.0', lambda db: ...),   # 基础表结构
    ('1.0.0.28', lambda db: ...),  # prd_product_supplier_url
]

def _get_schema_version(db) -> str:
    # 从 version_info 表读取
    return db.execute(text("SELECT value FROM system_info WHERE key='schema_version'")).fetchone()[0]

def _run_migrations(db):
    current = _get_schema_version(db)
    for version, fn in MIGRATIONS:
        if version > current:
            fn(db)
            db.execute(text("UPDATE system_info SET value=:v WHERE key='schema_version'"), {'v': version})
```

### 6.3 前端与后端 Schema 版本一致性

前端 dist 和 exe 必须版本匹配：
- exe 的 `min_app_version` 声明其支持的最小前端版本
- CDN 的 `version.json` 包含 `min_app_version`
- 不满足版本要求时，exe 拒绝下载新前端，退回缓存或内置版本

---

## 7. 打包配置

### 7.1 PyInstaller spec 更新

```python
# PI-Manager-Server.spec 新增内容
a = Analysis(
    ['run_qt.py'],  # 新增 Qt 入口脚本
    ...
    hiddenimports=[
        'uvicorn', 'fastapi', 'sqlalchemy', 'pymysql',
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWebEngineWidgets',
        'pywebchannel',  # QWebChannel JS 文件
    ],
)

# 打包内置前端兜底
dist_path = os.path.join(os.path.dirname(sys.executable), 'dist')
if not os.path.exists(dist_path):
    import shutil
    shutil.copytree(
        os.path.join(sys._MEIPASS, 'frontend_dist'),
        dist_path,
        dirs_exist_ok=True,
    )
```

### 7.2 前端 vite.config.ts 适配

由于 PyQt5 WebEngine 的 Chromium 内核版本可能较旧（例如 PyQt5 v5.15 使用 Chrome 83 内核），前端构建产物必须适配旧版 JS 语法（防止出现可选链 `?.`、空值合并 `??` 或顶层 `await` 导致的白屏 SyntaxError）：

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  base: './',  // 确保相对路径，file:// 协议下运行必须
  plugins: [
    // 增加 Legacy 浏览器兼容插件支持，确保兼容旧版 JS 特性
    legacy({
      targets: ['chrome >= 80', 'es2015'],
      additionalLegacyPolyfills: ['regenerator-runtime/runtime']
    })
  ],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    target: 'chrome80' // 指定编译目标，避免采用过新语法的 esnext
  },
})
```

---

## 8. 新增文件清单

| 文件 | 用途 |
|------|------|
| `backend/qt_bridge.py` | QWebChannel API 暴露（业务方法 + 生命周期） |
| `backend/run_qt.py` | Qt 应用入口（替代 run.py 的 Qt 模式） |
| `backend/frontend_manager.py` | 前端包下载、解压、原子更新 |
| `backend/check_update.py` | 版本检测、SHA-256 校验 |
| `frontend/src/api/nativeBridge.ts` | 扩展支持所有业务 QWebChannel 接口 |
| `frontend/src/api/base.ts` | 通信模式自动切换（QWebChannel vs axios） |
| `frontend/src/utils/modeDetector.ts` | 加载模式检测与降级处理 |

---

## 9. 实施里程碑（建议）

### M1: 基础框架（纯离线）
- `run_qt.py` 启动 Qt WebEngine，加载内置 `_MEIPASS/dist/index.html`
- `qt_bridge.py` 暴露基础 API
- 前端 `nativeBridge.ts` 支持 QWebChannel 调用
- 前端通信模式自动切换

### M2: 前端更新机制
- CDN 版本检测
- 基于版本目录隔离的下载/解压（避免 Windows 文件锁）
- 回滚保护（config.json active_version 切换）
- 前端刷新提示

### M3: 数据库迁移集成
- `MIGRATIONS` 注册表
- 启动时自动执行增量更新

### M4: 降级与异常处理
- QWebChannel 初始化失败降级
- 损坏 dist-v* 目录的回滚
- SHA-256 校验失败处理

---

## 10. 已知限制与性能开销

- **CDN 服务器需自行搭建或使用第三方服务**
- **离线模式功能受限于 QWebChannel 暴露的 API 范围**，复杂查询可能需要补充接口
- **Chromium 版本兼容性要求**：需要通过 Vite legacy 插件保证打包产物不包含 ES 新语法特性。
- **内存占用开销**：PyQt5 WebEngine 会拉起多个 Chromium 辅助进程，应用常驻内存开销一般在 100MB - 300MB 之间。
- **首次部署需要人工确认 exe 版本与前端版本匹配**
