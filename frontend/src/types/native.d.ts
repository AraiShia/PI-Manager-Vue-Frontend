// QWebChannel 类型声明

interface QWebChannelTransport {
  send(data: any): void
  onmessage: (data: any) => void
}

interface QWebChannel {
  objects: {
    nativeBridge: NativeBridge
  }
}

export interface NativeBridge {
  selectFile(filter: string): Promise<string>
  saveFile(defaultName: string): Promise<string>
  readExcel(path: string): Promise<any[]>
  writeExcel(path: string, data: any[]): Promise<boolean>
  showNotification(message: string): void
  getAppVersion(): Promise<string>
  getAppVersionName(): Promise<string>
  readFileAsBase64?(path: string): Promise<string>
  uploadImage?(localPath: string, uploadUrl: string): Promise<{ url: string }>
  versionAvailable: { connect(callback: (version: string) => void): void }
  fileSelected: { connect(callback: (path: string) => void): void }
}

declare global {
  interface Window {
    QWebChannel: any
    qtWebChannelTransport: QWebChannelTransport
  }
}

export {}
