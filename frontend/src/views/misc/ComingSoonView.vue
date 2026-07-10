<template>
  <main class="coming-soon">
    <section class="coming-soon__card">
      <el-tag type="warning" effect="light">迁移中</el-tag>
      <h1>{{ title }}</h1>
      <p>该模块正在从桌面客户端迁移到 Web。</p>
      <dl>
        <div><dt>原始入口</dt><dd>{{ source }}</dd></div>
        <div><dt>负责模块</dt><dd>{{ owner }}</dd></div>
      </dl>
      <div class="coming-soon__actions">
        <el-button @click="router.go(0)">刷新页面</el-button>
        <el-button type="primary" @click="router.push('/orders')">返回订单总表</el-button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const title = computed(() => String(route.meta.title || '功能开发中'))
const source = computed(() => String(route.meta.source || '桌面客户端'))
const owner = computed(() => String(route.meta.owner || '业务模块'))
</script>

<style scoped>
.coming-soon {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 48px 24px;
  background: #f5f7fa;
  min-height: 100%;
}
.coming-soon__card {
  background: #fff;
  border-radius: 8px;
  padding: 40px 48px;
  max-width: 640px;
  width: 100%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.coming-soon__card h1 {
  margin: 16px 0 8px;
  font-size: 24px;
  color: #1f2937;
}
.coming-soon__card p {
  color: #6b7280;
  margin: 0 0 24px;
}
.coming-soon__card dl {
  margin: 0 0 24px;
}
.coming-soon__card dl > div {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 14px;
}
.coming-soon__card dt {
  color: #9ca3af;
  min-width: 80px;
}
.coming-soon__card dd {
  color: #374151;
  margin: 0;
}
.coming-soon__actions {
  display: flex;
  gap: 12px;
}
</style>
