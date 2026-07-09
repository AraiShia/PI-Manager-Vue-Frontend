<template>
  <div class="water-bill-uploader">
    <input
      ref="fileInputRef"
      type="file"
      accept=".jpg,.jpeg,.png,.pdf"
      style="display: none"
      @change="onFileChange"
    />

    <!-- 有图片时显示预览 -->
    <div v-if="modelValue" class="preview-box">
      <el-image
        :src="modelValue"
        :preview-src-list="[modelValue]"
        fit="contain"
        class="preview-image"
        preview-teleported
      />
      <div class="preview-actions">
        <el-button size="small" @click="triggerUpload">
          <el-icon><Upload /></el-icon>
          替换
        </el-button>
        <el-button size="small" type="danger" @click="onDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 无图片时显示上传区域 -->
    <div
      v-else
      class="upload-trigger"
      @click="triggerUpload"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">点击上传或拖拽水单图片</div>
      <div class="upload-hint">支持 JPG、PNG、PDF，大小不超过 10MB</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Delete } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

const fileInputRef = ref<HTMLInputElement>()
const isDragging = ref(false)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
const MAX_SIZE = 10 * 1024 * 1024 // 10MB

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    processFile(input.files[0])
  }
  // 重置 input 以允许重复选择同一文件
  input.value = ''
}

function onDragOver(e: DragEvent) {
  isDragging.value = true
}

function onDragLeave(_e: DragEvent) {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    processFile(files[0])
  }
}

function processFile(file: File) {
  // 校验文件类型
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、PDF 格式')
    return
  }

  // 校验文件大小
  if (file.size > MAX_SIZE) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  // 读取文件为 base64
  const reader = new FileReader()
  reader.onload = (e) => {
    const base64 = e.target?.result as string
    emit('update:modelValue', base64)
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsDataURL(file)
}

function onDelete() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.water-bill-uploader {
  width: 100%;
}

.upload-trigger {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.upload-trigger:hover {
  border-color: #409eff;
  background: #f0f7ff;
}

.upload-icon {
  font-size: 40px;
  color: #909399;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.preview-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-image {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.preview-actions {
  display: flex;
  gap: 8px;
}
</style>
