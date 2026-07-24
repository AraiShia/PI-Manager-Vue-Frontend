<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onVersionAvailable } from '@/api/nativeBridge'
import { ElMessageBox } from 'element-plus'

// onVersionAvailable 内部等待 bridgeReady，无需在 App.vue 中判断 isBridgeAvailable()。
// 如果 bridge 不可用，onVersionAvailable 不会触发回调，升级通知静默忽略。
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
      const b = (window as any).nativeBridge
      if (b && b.trigger_refresh) {
        await b.trigger_refresh()
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
