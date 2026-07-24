import './utils/enforceHttps'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/hide-number-spinner.css'
import './styles/dialog-overlay.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import { nativeBridge } from '@/api/nativeBridge'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 在挂载前启动 QWebChannel 初始化（不阻塞挂载）。
// 所有需要 bridge 的业务代码在调用前 await bridgeReady。
// App.vue 中的 onVersionAvailable 监听也依赖 bridgeReady。
nativeBridge.init().then((ok) => {
  console.log(`[Bootstrap] Native bridge ${ok ? 'initialized' : 'not available'}`)
})

app.mount('#app')
