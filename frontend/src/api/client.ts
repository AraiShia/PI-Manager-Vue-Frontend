import axios from 'axios'
import { ElMessage } from 'element-plus'
import { normalizeApiBase } from './endpoints'
import { detectAppMode } from '../utils/modeDetector'
import { call as callNativeBridge } from './nativeBridge'

// 离线模式下的 RPC 路由映射表，将 HTTP 请求路径和方法映射到 Python 端的相应方法上
function matchRpcRoute(url: string, method: string) {
  // 标准化 URL 路径，移除首尾斜杠
  const cleanUrl = url.replace(/^\/+|\/+$/g, '')
  const methodUpper = method.toUpperCase()

  // 1. GET /api/suppliers/ -> 查询供应商列表
  if (cleanUrl === 'api/suppliers' && methodUpper === 'GET') {
    return {
      rpcMethod: 'suppliers.list',
      mapParams: (config: any) => config.params || {}
    }
  }

  // 2. POST /api/suppliers/ -> 新建供应商
  if (cleanUrl === 'api/suppliers' && methodUpper === 'POST') {
    return {
      rpcMethod: 'suppliers.create',
      mapParams: (config: any) => config.data || {}
    }
  }

  // 3. POST /api/suppliers/find-or-create -> 查找或创建供应商
  if (cleanUrl === 'api/suppliers/find-or-create' && methodUpper === 'POST') {
    return {
      rpcMethod: 'suppliers.findOrCreate',
      mapParams: (config: any) => config.data || {}
    }
  }

  // 4. GET /api/suppliers/provinces -> 获取省份列表
  if (cleanUrl === 'api/suppliers/provinces' && methodUpper === 'GET') {
    return {
      rpcMethod: 'suppliers.getProvinces',
      mapParams: () => ({})
    }
  }

  // 5. GET /api/suppliers/cities/:province -> 获取城市列表
  const citiesMatch = cleanUrl.match(/^api\/suppliers\/cities\/(.+)$/)
  if (citiesMatch && methodUpper === 'GET') {
    const province = decodeURIComponent(citiesMatch[1])
    return {
      rpcMethod: 'suppliers.getCities',
      mapParams: () => ({ province })
    }
  }

  // 6. PUT /api/suppliers/:id -> 更新供应商
  const putMatch = cleanUrl.match(/^api\/suppliers\/(\d+)$/)
  if (putMatch && methodUpper === 'PUT') {
    const id = parseInt(putMatch[1], 10)
    return {
      rpcMethod: 'suppliers.update',
      mapParams: (config: any) => ({ id, ...config.data })
    }
  }

  // 7. DELETE /api/suppliers/:id -> 删除供应商
  const deleteMatch = cleanUrl.match(/^api\/suppliers\/(\d+)$/)
  if (deleteMatch && methodUpper === 'DELETE') {
    const id = parseInt(deleteMatch[1], 10)
    return {
      rpcMethod: 'suppliers.delete',
      mapParams: () => ({ id })
    }
  }

  // 8. GET /api/pi -> PI 列表
  if (cleanUrl === 'api/pi' && methodUpper === 'GET') {
    return {
      rpcMethod: 'pi.list',
      mapParams: (config: any) => config.params || {}
    }
  }

  // 9. POST /api/purchase-orders -> 1688 线上采购
  if (cleanUrl === 'api/purchase-orders' && methodUpper === 'POST') {
    return {
      rpcMethod: 'purchase.createOnline',
      mapParams: (config: any) => config.data || {}
    }
  }

  // 10. GET /api/customers -> 客户列表
  if (cleanUrl === 'api/customers' && methodUpper === 'GET') {
    return {
      rpcMethod: 'customer.list',
      mapParams: (config: any) => config.params || {}
    }
  }

  // 11. GET /api/product-supplier-urls -> URL 历史列表
  if (cleanUrl === 'api/product-supplier-urls' && methodUpper === 'GET') {
    return {
      rpcMethod: 'productSupplierUrls.list',
      mapParams: (config: any) => config.params || {}
    }
  }

  // 12. POST /api/product-supplier-urls -> 新增 URL 历史
  if (cleanUrl === 'api/product-supplier-urls' && methodUpper === 'POST') {
    return {
      rpcMethod: 'productSupplierUrls.create',
      mapParams: (config: any) => config.data || {}
    }
  }

  return null
}

// QWebChannel 自定义 Axios 适配器，模拟 Axios 响应结构
const qwebchannelAdapter = async (config: any): Promise<any> => {
  return new Promise(async (resolve, reject) => {
    try {
      const matched = matchRpcRoute(config.url || '', config.method || 'GET')
      if (!matched) {
        return reject({
          message: `[离线模式] 路由未配置映射: ${config.method} ${config.url}`,
          config,
          response: {
            data: { message: `离线模式下路由未定义: ${config.url}`, success: false },
            status: 404,
            statusText: 'Not Found',
            headers: {},
            config
          }
        })
      }

      const params = matched.mapParams(config)
      // 调用 NativeBridge 的通用 RPC 槽方法
      const resultData = await callNativeBridge(matched.rpcMethod, params)

      resolve({
        data: resultData, // 返回原生数据（数组或对象），以匹配响应拦截器及现有业务层使用
        status: 200,
        statusText: 'OK',
        headers: {},
        config
      })
    } catch (error: any) {
      reject({
        message: error.message || '离线桥接调用失败',
        config,
        response: {
          data: { message: error.message || '离线桥接调用失败', success: false },
          status: 500,
          statusText: 'Internal Server Error',
          headers: {},
          config
        }
      })
    }
  })
}

function runtimeApiBase() {
  // 本地离线/在线模式下，支持读取 fallback_api_base 配置
  if (typeof localStorage !== 'undefined') {
    const customBase = localStorage.getItem('fallback_api_base')
    if (customBase && customBase.trim()) {
      return normalizeApiBase(customBase.trim())
    }
  }

  // HTTPS 页面下：直接使用 window.location.origin
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    return window.location.origin
  }

  // HTTP 页面（包括本地 file:// + API 探测成功）或无 window 环境：
  // 优先使用 VITE_API_BASE_URL，否则回退到生产默认地址
  const base = normalizeApiBase(
    import.meta.env.VITE_API_BASE_URL || 'https://piapi.wakabashia.tj.cn'
  )
  return base
}

const client = axios.create({
  baseURL: runtimeApiBase(),
  timeout: 30000,
  // 注入自定义适配器，支持离线/在线/Web 三态机制
  adapter: (config) => {
    const mode = detectAppMode()

    // 1. 本地纯离线模式：只走 QWebChannel RPC 桥接
    if (mode === 'local-offline') {
      return qwebchannelAdapter(config)
    }

    // 2. 本地在线模式或远程 Web 模式：走标准 HTTP XHR 请求
    // local-online 模式下若配置了映射路由且网络断开，可自动降级到 RPC
    const defaultAdapter = axios.defaults.adapter
    if (typeof defaultAdapter === 'function') {
      return defaultAdapter(config)
    }
    // 兼容 Axios 1.x 自定义适配器解析
    const xhrAdapter = axios.getAdapter ? axios.getAdapter('xhr') : (axios as any).adapters?.xhr
    if (typeof xhrAdapter === 'function') {
      return xhrAdapter(config)
    }
    throw new Error('无法定位默认的 Axios 适配器')
  }
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
