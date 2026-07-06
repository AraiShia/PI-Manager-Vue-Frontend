<template>
  <div id="native-bridge-init" style="display:none"></div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { initNativeBridge } from '@/api/nativeBridge'

onMounted(() => {
  if (window.QWebChannel && window.qtWebChannelTransport) {
    new window.QWebChannel(window.qtWebChannelTransport, (channel: any) => {
      initNativeBridge(channel)
    })
  } else {
    console.warn('[NativeBridge] QWebChannel not available (running outside PyQt)')
  }
})
</script>
