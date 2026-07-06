// ============================================================
// API 基础工具
// 文件：src/api/base.ts
// 用途：统一管理 API 基础地址，支持：
//   1. 浏览器开发：Vite 代理转发 /api/*
//   2. 外部部署：VITE_API_BASE_URL 环境变量
//   3. PyQt 集成：URL 参数 ?apiBase=xxx
// ============================================================

/**
 * 从 URL 参数获取 apiBase
 * 用于 PyQt 等外部容器动态传入
 */
function getUrlApiBase(): string {
  const params = new URLSearchParams(window.location.search)
  return params.get('apiBase') || ''
}

/**
 * 后端 API 基础地址
 * 优先级：URL参数 > 环境变量 > 空（相对路径）
 */
const ENV_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim()
const RAW_BASE = getUrlApiBase() || ENV_BASE

/**
 * 拼接一个完整的 API URL
 * @param path 后端路径，以 / 开头，例如 '/api/customers/'
 */
export function apiUrl(path: string): string {
  if (!path) return RAW_BASE || '/'
  if (/^https?:\/\//i.test(path)) return path
  if (!RAW_BASE) return path
  // 避免双斜杠
  const left = RAW_BASE.replace(/\/+$/, '')
  const right = path.replace(/^\/+/, '')
  return `${left}/${right}`
}

/**
 * 原始 base 地址（不拼接）
 */
export const API_BASE_URL = RAW_BASE
