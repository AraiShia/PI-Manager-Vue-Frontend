import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const version = ref('')
  const appName = ref('PI Manager')
  const isConnected = ref(false)

  async function fetchVersion() {
    try {
      const { getAppVersion } = await import('@/api/nativeBridge')
      version.value = await getAppVersion()
      isConnected.value = true
    } catch {
      version.value = 'dev'
      isConnected.value = false
    }
  }

  return { version, appName, isConnected, fetchVersion }
})
