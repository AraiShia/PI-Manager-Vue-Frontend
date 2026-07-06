# Vue 前端配置指南

## 环境配置

### 开发环境 `.env.development`

```bash
# API 基础地址（fetch/axios 请求时拼接的前缀）
VITE_API_BASE_URL=http://localhost:8000

# Vite 开发服务器代理目标
VITE_API_TARGET=http://localhost:8000
```

### 生产环境 `.env.production`

```bash
# 前后端分离部署，Vue 加载地址
VITE_API_BASE_URL=https://piapi.wakabashia.tj.cn
VITE_API_TARGET=https://piapi.wakabashia.tj.cn
```

### PyQt 动态传入 API 地址

Vue 支持通过 URL 参数 `?apiBase=` 动态指定 API 地址：

```
https://your-vue-domain.com/orders?apiBase=https://your-api-domain.com
```

**优先级**：URL 参数 `?apiBase=` > 环境变量 `VITE_API_BASE_URL` > 空（相对路径）

## 常用命令

```bash
# 安装依赖
npm install

# 开发模式启动
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API 调用封装
│   │   ├── base.ts       # 基础配置
│   │   ├── client.ts     # HTTP 客户端
│   │   ├── nativeBridge.ts  # PyQt 桥接
│   │   └── orderSummary.ts  # 订单 API
│   ├── components/      # Vue 组件
│   │   └── order/          # 订单相关组件
│   ├── composables/     # 组合式函数
│   ├── constants/       # 常量定义
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia 状态管理
│   ├── types/          # TypeScript 类型
│   └── views/          # 页面视图
│       └── order/          # 订单页面
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .env.development / .env.production
```

## API 代理配置

`vite.config.ts` 中的代理配置：

```typescript
server: {
  port: 5173,
  host: '0.0.0.0',
  proxy: {
    '/api': {
      target: apiTarget,  // 来自 .env 文件
      changeOrigin: true,
    },
  },
},
```

开发模式下，所有 `/api/*` 请求会被代理到指定的后端地址。

## 与 PyQt 集成

通过 `NativeBridge` 实现 Vue 与 PyQt 的通信：

```typescript
import { nativeBridge } from '@/api/nativeBridge'

// 调用 PyQt 文件对话框
const filePath = await nativeBridge.selectFile('Excel 文件 (*.xlsx *.xls)')

// 读取 Excel
const data = await nativeBridge.readExcel(filePath)

// 调用 PyQt 写入 Excel
await nativeBridge.writeExcel(savePath, exportData)
```

## 构建产物

- 开发模式：`npm run dev` → http://localhost:5173
- 生产构建：`npm run build` → `dist/` 目录

构建产物可部署到：
- 静态托管（Vercel、Netlify 等）
- Nginx 静态服务
- PyQt QWebEngineView 直接加载
