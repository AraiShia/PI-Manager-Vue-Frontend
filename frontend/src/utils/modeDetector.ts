/**
 * 运行模式检测器 (Mode Detector)
 * 
 * 符合 Google 编程规范，包含详细的中文注释。
 * 用于区分前端运行的三种状态：
 * - local-offline: 本地 file:// 协议加载 + 离线使用本地 SQLite (通过 QWebChannel 桥接)
 * - local-online: 本地 file:// 协议加载 + 在线使用远程服务器 API (QWebChannel 仍可用于文件导出等原生交互)
 * - remote-web: 常规 HTTPS/HTTP 网页加载 + 远程 API (无 Native 桥接功能)
 */

export type AppMode = 'local-offline' | 'local-online' | 'remote-web'

/**
 * 检测当前前端运行模式
 * 
 * @returns {AppMode} 当前运行模式
 */
export function detectAppMode(): AppMode {
  // 如果处于服务端渲染或非浏览器环境，默认归为远程 Web
  if (typeof window === 'undefined') {
    return 'remote-web'
  }

  // 1. 如果加载协议不是 file://，则是标准的 Web 远程部署
  if (window.location.protocol !== 'file:') {
    return 'remote-web'
  }

  // 2. 检查本地离线标志与浏览器网络状态
  // 用户可手动在 localStorage 设置 app_offline_mode 强制离线调试
  const forceOffline = localStorage.getItem('app_offline_mode') === 'true'
  const isNetworkOffline = !navigator.onLine

  if (forceOffline || isNetworkOffline) {
    return 'local-offline'
  }

  return 'local-online'
}

/**
 * 判断是否运行在 PyQt5 WebEngine 的 Native 客户端内
 * 
 * @returns {boolean} 是否为本地 file:// 加载
 */
export function isNativeShell(): boolean {
  return typeof window !== 'undefined' && window.location.protocol === 'file:'
}
