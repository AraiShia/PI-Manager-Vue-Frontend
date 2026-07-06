// QWebChannel JS 端封装
import type { NativeBridge } from '@/types/native'

let bridge: NativeBridge | null = null
let initPromise: Promise<void> | null = null

export function initNativeBridge(channel: any) {
  bridge = channel.objects.nativeBridge
  console.log('[NativeBridge] initialized')
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
  if (initPromise) {
    return initPromise
  }

  initPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      reject(new Error('Window not available'))
      return
    }

    if (window.QWebChannel && window.qtWebChannelTransport) {
      new window.QWebChannel(window.qtWebChannelTransport, (channel: any) => {
        initNativeBridge(channel)
        resolve()
      })
    } else {
      reject(new Error('QWebChannel not available'))
    }
  })

  return initPromise
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

  async selectFile(filter: string): Promise<string> {
    return getBridge().selectFile(filter)
  },

  async saveFile(defaultName: string): Promise<string> {
    return getBridge().saveFile(defaultName)
  },

  async readExcel(path: string): Promise<any[]> {
    return getBridge().readExcel(path)
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
    const b = getBridge()
    if (b.versionAvailable && b.versionAvailable.connect) {
      b.versionAvailable.connect(callback)
    }
  },

  onFileSelected(callback: (path: string) => void) {
    const b = getBridge()
    if (b.fileSelected && b.fileSelected.connect) {
      b.fileSelected.connect(callback)
    }
  },
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
