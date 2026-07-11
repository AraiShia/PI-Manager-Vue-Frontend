// ============================================================
// API 基础工具
// 文件：src/api/base.ts
// 用途：统一管理 API 基础地址，让所有请求（axios / fetch）走同一来源
// ============================================================

/**
 * 后端 API 基础地址
 *  - 浏览器开发：Vite 代理转发 /api/*，因此可留空走相对路径
 *  - 部署/PyQt：设置 VITE_API_BASE_URL 指向真实后端
 */
const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim()
const ASSET_BASE = (import.meta.env.VITE_ASSET_BASE_URL || RAW_BASE || '').trim()

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

export function assetUrl(path: string | null | undefined): string {
  if (!path) return ''
  const value = path.trim()
  if (!value) return ''
  if (value.startsWith('data:') || value.startsWith('blob:')) return value
  if (/^https?:\/\//i.test(value)) {
    return value.replace(/^http:\/\/(piapi\.wakabashia\.tj\.cn)/i, 'https://$1')
  }
  if (!ASSET_BASE) return value
  const left = ASSET_BASE.replace(/\/+$/, '')
  const right = value.replace(/^\/+/, '')
  return `${left}/${right}`
}
