import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8001'

  return {
    // 确保相对路径，file:// 协议运行下必需
    base: './',
    plugins: [
      vue(),
      // Legacy 插件：生成 ES2015 polyfill bundle（兼容 PyQt5 WebEngine Chrome 83 内核）
      // Chrome 83 不支持 ES2020 可选链 / 空值合并 / 顶层 await
      // targets chrome>=83 等价于 PyQt5 v5.15 的 Chromium 内核版本
      legacy({
        targets: ['chrome >= 83'],
        additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
      }),
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 5173,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      // legacy 插件会自动将 build.target 设为 chrome>=83，
      // 无需单独指定；两者并存会导致 plugin-legacy 警告
    },
  }
})
