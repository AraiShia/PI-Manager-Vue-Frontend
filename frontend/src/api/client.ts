import axios from 'axios'
import { ElMessage } from 'element-plus'
import { normalizeApiBase } from './endpoints'

function runtimeApiBase() {
  // HTTPS 页面下：直接使用 window.location.origin，避免任何环境变量配错导致 Mixed Content
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    return window.location.origin
  }
  const base = normalizeApiBase(import.meta.env.VITE_API_BASE_URL || '')
  if (
    typeof window !== 'undefined'
    && window.location.protocol === 'https:'
    && /^https?:\/\/piapi\.wakabashia\.tj\.cn/i.test(base)
  ) {
    return window.location.origin
  }
  return base
}

const client = axios.create({
  baseURL: runtimeApiBase(),
  timeout: 30000,
})

client.interceptors.request.use(
  config => {
    if (config.baseURL) {
      config.baseURL = normalizeApiBase(config.baseURL)
    }
    if (config.url && /^http:\/\//i.test(config.url)) {
      config.url = normalizeApiBase(config.url)
    }
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

client.interceptors.response.use(
  response => {
    const payload = response.data
    // 兼容三种情况：
    //   1. {code:200, data:...}       -> 成功
    //   2. {success:true, ...}        -> 成功（PUT /api/pi/items/{id} 等）
    //   3. 没有 code/success 标记的   -> 默认视为成功，避免误报（很多 DELETE/204 后是空 payload）
    const codeOk = payload && Object.prototype.hasOwnProperty.call(payload, 'code') && payload.code === 200
    const successOk = payload && Object.prototype.hasOwnProperty.call(payload, 'success') && payload.success === true
    const noMark = payload && !Object.prototype.hasOwnProperty.call(payload, 'code') && !Object.prototype.hasOwnProperty.call(payload, 'success')
    if (payload && !codeOk && !successOk && !noMark) {
      ElMessage.error(payload.message || '请求失败')
      return Promise.reject(new Error(payload.message))
    }
    // 保持 axios 原始 response 结构，调用方统一通过 res.data 读取
    return response
  },
  error => {
    const detail = error.response?.data?.detail
    const message = error.response?.data?.message
      || (typeof detail === 'string' ? detail : undefined)
      || error.message
      || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default client
