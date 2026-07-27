// QWebChannel 类型声明

export interface ExcelReadResult {
  task_id: string
  ok: boolean
  data: any[]
  error: string
}

export interface NativeBridge {
  // RPC 统一调用
  call(method: string, paramsJson: string): Promise<string>
  // 文件对话框
  selectFile(filter: string): Promise<string>
  saveFile(defaultName: string): Promise<string>
  // Excel（异步版）：立即返回 task_id，结果通过 excelReadComplete 信号
  readExcel(path: string): string
  // 事件信号
  versionAvailable: { connect(callback: (version: string) => void): void }
  fileSelected: { connect(callback: (path: string) => void): void }
  // Excel 异步读取完成信号
  excelReadComplete: {
    connect(handler: (result: ExcelReadResult) => void): void
    disconnect(handler: Function): void
  }
  // 文件操作
  writeExcel(path: string, data: any[]): Promise<boolean>
  showNotification(message: string): void
  getAppVersion(): Promise<string>
  getAppVersionName(): Promise<string>
  readFileAsBase64?(path: string): Promise<string>
  uploadImage?(localPath: string, uploadUrl: string): Promise<{ url: string }>
}

declare global {
  interface Window {
    QWebChannel: any
    // Qt 标准注入名称：window.qt.webChannelTransport
    qt: {
      webChannelTransport: {
        send(data: any): void
        onmessage: (data: any) => void
      }
    }
  }
}

export {}
