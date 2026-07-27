<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { isBridgeAvailable, onVersionAvailable, getBridge } from '@/api/nativeBridge'
import { ElMessageBox } from 'element-plus'

onMounted(() => {
  // 当运行在 PyQt/PySide6 原生壳中且桥接就绪时，监听热更新版本发布通知
  try {
    if (isBridgeAvailable()) {
      onVersionAvailable((version: string) => {
        ElMessageBox.confirm(
          `检测到系统前端新版本 ${version} 已完成下载，是否立即刷新页面载入新版本？`,
          '热更新就绪',
          {
            confirmButtonText: '立即刷新',
            cancelButtonText: '稍后处理',
            type: 'info',
          }
        ).then(async () => {
          try {
            const b = getBridge()
            if (b && (b as any).trigger_refresh) {
              await (b as any).trigger_refresh()
            } else {
              window.location.reload()
            }
          } catch {
            window.location.reload()
          }
        }).catch(() => {
          // 用户忽略或稍后处理
        })
      })
    }
  } catch (e) {
    console.debug('[App] 原生版本更新监听不可用 (浏览器运行模式):', e)
  }
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
body {
  margin: 0;
  padding: 0;
}
</style>
