<template>
  <div id="native-bridge-init" style="display:none"></div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { initNativeBridge } from '@/api/nativeBridge'
import { ElMessageBox, ElMessage } from 'element-plus'

onMounted(() => {
  // Qt 标准注入名称：window.qt.webChannelTransport（不是 qtWebChannelTransport）
  const transport = (window as any).qt?.webChannelTransport
  if (window.QWebChannel && transport) {
    try {
      new window.QWebChannel(transport, (channel: any) => {
        initNativeBridge(channel)
      })
    } catch (e) {
      console.warn('[NativeBridge] QWebChannel 初始化异常:', e)
      handleFallbackPrompt()
    }
  } else {
    console.warn('[NativeBridge] QWebChannel 不可用 (浏览器或非 Native 环境)')
    if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
      handleFallbackPrompt()
    }
  }
})

function handleFallbackPrompt() {
  const hasLocalConfig = localStorage.getItem('fallback_api_base')
  if (!hasLocalConfig) {
    ElMessageBox.prompt(
      '当前处于本地文件模式但原生桥接未连接，请输入远程 API 服务器地址：',
      '配置 API 服务器',
      {
        confirmButtonText: '保存配置',
        cancelButtonText: '暂不设置',
        inputValue: 'https://piapi.wakabashia.tj.cn',
        inputPattern: /^https?:\/\/.+/i,
        inputErrorMessage: '请输入有效的 HTTP/HTTPS URL',
      }
    ).then(({ value }) => {
      if (value && value.trim()) {
        localStorage.setItem('fallback_api_base', value.trim())
        ElMessage.success('配置已保存，正在刷新应用...')
        setTimeout(() => window.location.reload(), 1000)
      }
    }).catch(() => {
      // 用户取消设置
    })
  }
}
</script>
