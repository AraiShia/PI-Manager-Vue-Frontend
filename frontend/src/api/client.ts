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
    // 失败标记：code != 200 或 success === false
    const codeIsError = payload && payload.code !== undefined && payload.code !== 200
    const successIsFalse = payload && payload.success === false
    if (codeIsError || successIsFalse) {
      ElMessage.error(payload?.message || '请求失败')
      return Promise.reject(new Error(payload?.message || '请求失败'))
    }
    // 其他所有情况（{code:200} / {success:true} / 无标记 / 空 payload）均视为成功
    return response
  },
  error => {
    // 忽略主动取消的请求（AbortError / Cancel）
    if (error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
      return Promise.reject(error)
    }
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
