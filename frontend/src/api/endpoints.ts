// ============================================================
// API 端点统一配置
// 文件：src/api/endpoints.ts
// 用途：所有后端路径集中在此维护，切换 / 排查服务端只需改一个文件
// 规则：
//   - 路径以 / 开头，不带 baseURL（由 apiUrl() 或 axios baseURL 自动拼接）
//   - 含参数的路径用函数返回，例如 customers.detail(123)
//   - 新增端点请同步更新 ../docs/spec.md 第 5 节
// ============================================================

export const API_HOST = 'https://piapi.wakabashia.tj.cn' as const

// ----- 认证 -----
export const AUTH = {
  login: '/api/auth/login',
  logout: '/api/auth/logout',
  me: '/api/auth/me',
} as const

// ----- 客户 / 供应商 -----
export const CUSTOMERS = {
  list: '/api/customers/',
  detail: (id: number) => `/api/customers/${id}`,
  create: '/api/customers/',
  update: (id: number) => `/api/customers/${id}`,
  remove: (id: number) => `/api/customers/${id}`,
  toggleStatus: (id: number) => `/api/customers/${id}/status`,
  search: '/api/customers/search',
  contacts: (id: number) => `/api/customers/${id}/contacts`,
  createContact: (id: number) => `/api/customers/${id}/contacts`,
  updateContact: (id: number, cid: number) => `/api/customers/${id}/contacts/${cid}`,
  removeContact: (id: number, cid: number) => `/api/customers/${id}/contacts/${cid}`,
} as const

export const SUPPLIERS = {
  list: '/api/suppliers/',
  detail: (id: number) => `/api/suppliers/${id}`,
  create: '/api/suppliers/',
  update: (id: number) => `/api/suppliers/${id}`,
  remove: (id: number) => `/api/suppliers/${id}`,
  provinces: '/api/suppliers/provinces',
  cities: (province: string) =>
    `/api/suppliers/cities/${encodeURIComponent(province)}`,
} as const

// ----- 产品 -----
export const CUSTOMER_PRODUCTS = {
  list: '/api/customer-products',
  detail: (id: number) => `/api/customer-products/${id}`,
  create: '/api/customer-products',
  update: (id: number) => `/api/customer-products/${id}`,
  remove: (id: number) => `/api/customer-products/${id}`,
} as const

export const PRODUCT_CATEGORIES = {
  list: '/api/product-categories/',
  detail: (id: number | string) => `/api/product-categories/${id}`,
  create: '/api/product-categories/',
  update: (id: number | string) => `/api/product-categories/${id}`,
  remove: (id: number | string) => `/api/product-categories/${id}`,
  nextCode: '/api/product-categories/next-code',
} as const

export const PRODUCT_CUSTOMER = {
  search: '/api/product-customer/search',
} as const

// ----- 订单 / PI -----
export const ORDERS_BFF = {
  list: '/api/bff/orders',
  detail: (id: number) => `/api/bff/orders/${id}`,
  create: '/api/bff/orders',
  update: (id: number) => `/api/bff/orders/${id}`,
  remove: (id: number) => `/api/bff/orders/${id}`,
  importItems: (orderId: number) => `/api/bff/orders/${orderId}/import-items`,
  dashboard: '/api/bff/orders/dashboard',
  fullDetail: (orderId: number) => `/api/bff/orders/${orderId}/full-detail`,
  supplementItems: (orderId: number) => `/api/orders/${orderId}/supplement-items`,
  import: '/api/orders/import',
} as const

export const PI = {
  detail: (id: number) => `/api/pi/${id}`,
  create: '/api/pi/',
  remove: (id: number) => `/api/pi/${id}`,
  status: (piId: number) => `/api/pi/${piId}/status`,
  generatePi: (orderId: number) => `/api/pi/${orderId}/generate-pi`,
  formalRecordExists: (orderId: number) =>
    `/api/pi/${orderId}/formal-record/exists`,
  saveFormalRecord: (orderId: number) => `/api/pi/${orderId}/formal-record`,
  inboundBatch: (piId: number) => `/api/pi/${piId}/inbound-batch`,
  payments: (orderId: number) => `/api/pi/${orderId}/payments`,
} as const

export const PI_ITEMS = {
  update: (itemId: number) => `/api/pi/items/${itemId}`,
  remove: (itemId: number) => `/api/pi/items/${itemId}`,
  inbound: (itemId: number) => `/api/pi/items/${itemId}/inbound`,
} as const

// ----- 采购 -----
export const PURCHASE = {
  createOnline: '/api/purchase-orders/1688',
  createOffline: '/api/purchase-orders',
  list: '/api/purchase-orders',
  confirm: (id: number) => `/api/purchase-orders/${id}/confirm`,
  inbound: (id: number) => `/api/purchase-orders/${id}/inbound`,
  invoice: (id: number) => `/api/purchase-orders/${id}/invoice`,
  productLatest: (productId: number) =>
    `/api/purchase-orders/product/${productId}/latest`,
  recent1688Urls: (productId: number, limit: number = 5) =>
    `/api/purchase-orders/1688/recent-urls?product_id=${productId}&limit=${limit}`,
  exportContract: (id: number) => `/api/export/purchase/${id}/contract`,
} as const

// ----- 出货 -----
export const SHIPMENTS = {
  list: '/api/shipments/',
  detail: (id: number) => `/api/shipments/${id}`,
  shippableItems: '/api/shipments/shippable-items',
  createFromOrders: '/api/shipments/from-orders',
  confirm: (id: number) => `/api/shipments/${id}/confirm`,
} as const

// ----- 收款 -----
export const PAYMENTS = {
  receivables: '/api/payments/receivables',
  receivablesByPi: (piId: number) => `/api/payments/receivables/by-pi/${piId}`,
  receivableDetail: (id: number) => `/api/payments/receivables/${id}`,
} as const

// ----- 图片 -----
export const IMAGES = {
  upload: '/api/images/upload',
} as const

// ----- 数据迁移 -----
export const MIGRATIONS = {
  syncProductImages: '/api/migrations/sync-product-images',
} as const
