// ============================================================
// API 基础工具
// 文件：src/api/base.ts
// 用途：统一管理 API 基础地址，让所有请求（axios / fetch）走同一来源
// 端点常量请见 ./endpoints.ts
// ============================================================

import { normalizeApiBase } from './endpoints'

/**
 * 后端 API 基础地址
 *  - 浏览器开发：Vite 代理转发 /api/*，因此可留空走相对路径
 *  - 部署/PyQt：设置 VITE_API_BASE_URL 指向真实后端
 *
 * 默认值取自 ./endpoints.ts 中的 API_HOST，避免多处硬编码域名
 *
 * 注意：若误将 VITE_API_BASE_URL 配置为 http://，会被强制升级为 https://，
 * 避免浏览器 Mixed Content 拦截。
 */
function runtimeApiBase(raw: string) {
  // HTTPS 页面下：直接使用 window.location.origin，避免任何环境变量配错导致 Mixed Content
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    return window.location.origin
  }
  const base = normalizeApiBase(raw)
  if (
    typeof window !== 'undefined'
    && window.location.protocol === 'https:'
    && /^https?:\/\/piapi\.wakabashia\.tj\.cn/i.test(base)
  ) {
    return window.location.origin
  }
  return base
}

const RAW_BASE = runtimeApiBase(import.meta.env.VITE_API_BASE_URL || '')
const ASSET_BASE = normalizeApiBase(import.meta.env.VITE_ASSET_BASE_URL || RAW_BASE)

/**
 * 拼接一个完整的 API URL
 * @param path 后端路径（推荐从 ./endpoints 导入），例如 '/api/customers/'
 *
 * 如果 RAW_BASE 已是绝对 URL（含 host），即使 path 也是绝对 URL，
 * 也会优先使用 path（兼容旧代码）；仅当 path 为相对路径时才拼接。
 */
export function apiUrl(path: string): string {
  if (!path) return RAW_BASE || '/'
  let url: string
  // 如果 path 已是完整 URL，直接返回（不再拼接 base）
  if (/^https?:\/\//i.test(path)) {
    url = path
  } else if (!RAW_BASE) {
    return path
  } else {
    // 避免双斜杠
    const left = RAW_BASE.replace(/\/+$/, '')
    const right = path.replace(/^\/+/, '')
    url = `${left}/${right}`
  }
  // 防御：RAW_BASE 是 https 时强制把输出升级为 https，避免 Mixed Content
  if (/^https?:\/\//i.test(RAW_BASE) && /^http:\/\//i.test(url)) {
    url = url.replace(/^http:\/\//i, 'https://')
  }
  return url
}

/**
 * 原始 base 地址（不拼接）
 */
export const API_BASE_URL = RAW_BASE

export function assetUrl(path: string | null | undefined): string {
  if (!path) return ''
  const value = path.trim()
  if (!value) return ''
  if (value.startsWith('data:') || value.startsWith('blob:')) return value
  if (/^https?:\/\//i.test(value)) {
    // 强制升级 http → https
    return value.replace(/^http:\/\//i, 'https://')
  }
  if (!ASSET_BASE) return value
  const left = ASSET_BASE.replace(/\/+$/, '')
  const right = value.replace(/^\/+/, '')
  return `${left}/${right}`
}
