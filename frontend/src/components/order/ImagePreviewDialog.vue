<template>
  <el-dialog
    v-model="visible"
    title="图片预览"
    width="90vw"
    top="5vh"
    :close-on-click-modal="true"
    class="image-preview-dialog"
  >
    <div class="image-preview-wrapper" ref="wrapperRef" @wheel.prevent="onWheel" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp">
      <img ref="imgRef" :src="src" class="preview-img" :style="imgStyle" alt="原图预览" @load="onLoad" @error="onError" draggable="false" />
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ modelValue: boolean; src: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const wrapperRef = ref<HTMLElement>()
const imgRef = ref<HTMLImageElement>()
const translateX = ref(0)
const translateY = ref(0)
const scale = ref(1)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)
const loaded = ref(false)
const error = ref(false)

const imgStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  cursor: isDragging.value ? 'grabbing' : loaded.value ? 'grab' : 'default',
}))

function onLoad() {
  loaded.value = true
  error.value = false
  resetPosition()
}

function onError() {
  error.value = true
  loaded.value = false
}

function resetPosition() {
  translateX.value = 0
  translateY.value = 0
  scale.value = 1
}

function onMouseDown(e: MouseEvent) {
  if (!loaded.value) return
  isDragging.value = true
  startX.value = e.clientX - translateX.value
  startY.value = e.clientY - translateY.value
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  translateX.value = e.clientX - startX.value
  translateY.value = e.clientY - startY.value
}

function onMouseUp() {
  isDragging.value = false
}

// 滚轮缩放
function onWheel(e: WheelEvent) {
  e.preventDefault()
  if (!loaded.value) return
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.min(Math.max(scale.value * delta, 0.5), 3)
  scale.value = newScale
  if (newScale <= 1) resetPosition()
}

defineExpose({ resetPosition: resetPosition })
</script>

<style scoped>
.image-preview-dialog :deep(.el-dialog__body) {
  padding: 0;
  overflow: hidden;
  background: #1a1a1a;
}

.image-preview-wrapper {
  width: 100%;
  height: 75vh;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  position: relative;
  user-select: none;
}

.image-preview-wrapper::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.image-preview-wrapper::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.05s ease-out;
  display: block;
  min-width: 200px;
  min-height: 200px;
}
</style>
