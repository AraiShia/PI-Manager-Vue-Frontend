// QWebChannel JS 端封装
import type { NativeBridge } from '@/types/native'

let bridge: NativeBridge | null = null
let _resolveBridgeReady: (() => void) | null = null

/**
 * 全局 bootstrap promise。所有业务代码在发起离线请求前必须 await 此 promise。
 * 在 main.ts 中初始化，初始化完成后 resolve。
 */
export const bridgeReady = new Promise<void>((resolve) => {
  _resolveBridgeReady = resolve
})

export function initNativeBridge(channel: any) {
  bridge = channel.objects.nativeBridge
  console.log('[NativeBridge] initialized')
  if (_resolveBridgeReady) {
    _resolveBridgeReady()
    _resolveBridgeReady = null
  }
}

export function getBridge(): NativeBridge {
  if (!bridge) {
    throw new Error('NativeBridge not initialized. Ensure nativeBridge.init() has been called.')
  }
  return bridge
}

export function isBridgeAvailable(): boolean {
  return bridge !== null
}

async function initQWebChannel(): Promise<void> {
  // 已在初始化过程中，直接返回已解析的 bridgeReady
  if (bridge !== null) {
    return bridgeReady
  }

  if (typeof window === 'undefined') {
    throw new Error('Window not available')
  }

  // Qt 标准注入名称：window.qt.webChannelTransport（不是 qtWebChannelTransport）
  const transport = (window as any).qt?.webChannelTransport
  if (!window.QWebChannel || !transport) {
    throw new Error('QWebChannel not available')
  }

  return new Promise<void>((resolve, reject) => {
    new window.QWebChannel(transport, (channel: any) => {
      initNativeBridge(channel)
      resolve()
    })
  })
}

export const nativeBridge = {
  async init(): Promise<boolean> {
    try {
      await initQWebChannel()
      return true
    } catch {
      console.log('[NativeBridge] Running in browser mode (no native bridge)')
      return false
    }
  },

  get isAvailable(): boolean {
    return bridge !== null
  },

  /**
   * 统一 RPC 调用方法，将请求序列化并发送至 Python 端的 call 槽方法
   * 
   * @param {string} method 远程方法名，例如 "suppliers.list"
   * @param {any} params 方法参数，默认为空对象
   * @returns {Promise<any>} 返回 Python 执行完毕后的解析数据
   */
  async call(method: string, params: any = {}): Promise<any> {
    const b = getBridge()
    if (!b.call) {
      throw new Error(`本地桥接不支持 RPC 调用方法: ${method}`)
    }
    const paramsJson = JSON.stringify(params)
    const resultJson = await b.call(method, paramsJson)
    const result = JSON.parse(resultJson)
    if (result.success) {
      return result.data
    } else {
      throw new Error(result.error || '未知的本地 RPC 错误')
    }
  },

  async selectFile(filter: string): Promise<string> {
    return getBridge().selectFile(filter)
  },

  async saveFile(defaultName: string): Promise<string> {
    return getBridge().saveFile(defaultName)
  },

  async readExcel(path: string): Promise<{ taskId: string; data: any[]; error: string }> {
    // 异步读取：通过 bridgeReady 确保 bridge 可用，
    // 然后调用立即返回 task_id 的异步方法，并监听 excelReadComplete 信号获取结果。
    await bridgeReady
    const b = getBridge()
    const taskId: string = b.readExcel(path)

    return new Promise((resolve) => {
      // 一次性监听：读取完成后自动断开，避免内存泄漏
      const handler = (result: any) => {
        if (result.task_id === taskId) {
          if (b.excelReadComplete?.disconnect) {
            b.excelReadComplete.disconnect(handler)
          }
          resolve({
            taskId: result.task_id,
            data: result.data || [],
            error: result.error || '',
          })
        }
      }
      if (b.excelReadComplete?.connect) {
        b.excelReadComplete.connect(handler)
      } else {
        resolve({ taskId, data: [], error: 'excelReadComplete signal 不可用' })
      }
    })
  },

  async writeExcel(path: string, data: any[]): Promise<boolean> {
    return getBridge().writeExcel(path, data)
  },

  showNotification(message: string): void {
    getBridge().showNotification(message)
  },

  async getAppVersion(): Promise<string> {
    return getBridge().getAppVersion()
  },

  async getAppVersionName(): Promise<string> {
    return getBridge().getAppVersionName()
  },

  async readFileAsBase64(path: string): Promise<string> {
    const b = getBridge()
    if (!b.readFileAsBase64) {
      throw new Error('Native bridge does not support readFileAsBase64')
    }
    return b.readFileAsBase64(path)
  },

  async uploadImage(localPath: string, uploadUrl: string): Promise<{ url: string }> {
    const b = getBridge()
    if (b.uploadImage) {
      return b.uploadImage(localPath, uploadUrl)
    }
    // Fallback: read base64 and upload via fetch
    if (!b.readFileAsBase64) {
      throw new Error('Native bridge does not support image upload')
    }
    const base64 = await b.readFileAsBase64(localPath)
    const binary = Uint8Array.from(atob(base64), c => c.charCodeAt(0))
    const res = await fetch(uploadUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: binary,
    })
    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status} ${res.statusText}`)
    }
    return res.json()
  },

  onVersionAvailable(callback: (version: string) => void) {
    // 必须在 bridgeReady 后才能注册信号，否则 bridge 尚未初始化，信号永远收不到
    bridgeReady.then(() => {
      const b = getBridge()
      if (b.versionAvailable && b.versionAvailable.connect) {
        b.versionAvailable.connect(callback)
      }
    })
  },

  onFileSelected(callback: (path: string) => void) {
    const b = getBridge()
    if (b.fileSelected && b.fileSelected.connect) {
      b.fileSelected.connect(callback)
    }
  },
}

export async function call(method: string, params: any = {}): Promise<any> {
  return nativeBridge.call(method, params)
}

export async function selectFile(filter: string): Promise<string> {
  return getBridge().selectFile(filter)
}

export async function saveFile(defaultName: string): Promise<string> {
  return getBridge().saveFile(defaultName)
}

export async function readExcel(path: string): Promise<any[]> {
  return getBridge().readExcel(path)
}

export async function writeExcel(path: string, data: any[]): Promise<boolean> {
  return getBridge().writeExcel(path, data)
}

export function showNotification(message: string): void {
  getBridge().showNotification(message)
}

export async function getAppVersion(): Promise<string> {
  return getBridge().getAppVersion()
}

export async function getAppVersionName(): Promise<string> {
  return getBridge().getAppVersionName()
}

export function onVersionAvailable(callback: (version: string) => void) {
  const b = getBridge()
  if (b.versionAvailable && b.versionAvailable.connect) {
    b.versionAvailable.connect(callback)
  }
}

export function onFileSelected(callback: (path: string) => void) {
  const b = getBridge()
  if (b.fileSelected && b.fileSelected.connect) {
    b.fileSelected.connect(callback)
  }
}

// 离线模式供应商 URL 历史
export interface OfflineSupplierUrl {
  id: number
  product_id: number
  supplier_id: number | null
  supplier_name: string | null
  url: string
  display_name: string | null
  is_default: boolean
  created_at: string | null
}

export interface CreateSupplierUrlResult extends OfflineSupplierUrl {
  created: boolean
}

// 补充 productSupplierUrls 离线 RPC 封装
export async function listSupplierUrls(params: {
  product_id: number
  supplier_id?: number
  supplier_name?: string
}): Promise<OfflineSupplierUrl[]> {
  const result = await call('productSupplierUrls.list', params)
  return result as OfflineSupplierUrl[]
}

export async function createSupplierUrl(params: {
  product_id: number
  supplier_id: number
  supplier_name: string
  url: string
  display_name?: string
  is_default?: boolean
}): Promise<CreateSupplierUrlResult> {
  const result = await call('productSupplierUrls.create', params)
  return result as CreateSupplierUrlResult
}
