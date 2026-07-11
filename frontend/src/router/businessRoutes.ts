export interface BusinessRouteMeta {
  key: string
  path: string
  title: string
  source: string
  owner: string
  implemented: boolean
}

export const BUSINESS_ROUTES: readonly BusinessRouteMeta[] = [
  { key: 'products', path: '/products', title: '产品管理', source: 'Web 产品管理', owner: '产品模块', implemented: true },
  { key: 'customers', path: '/customers', title: '客户管理', source: '原 PyQt 客户管理', owner: '客户模块', implemented: false },
  { key: 'suppliers', path: '/suppliers', title: '供应商管理', source: '原 PyQt 供应商管理', owner: '供应商模块', implemented: false },
  { key: 'quotes', path: '/quotes', title: '报价管理', source: '原 PyQt 报价管理', owner: '报价模块', implemented: false },
  { key: 'pi', path: '/pi', title: 'PI 管理', source: '原 PyQt PI 管理', owner: 'PI 模块', implemented: false },
  { key: 'purchase', path: '/purchases', title: '采购管理', source: '原 PyQt 采购管理', owner: '采购模块', implemented: false },
  { key: 'shipment', path: '/shipments', title: '出货管理', source: 'Web 出货管理', owner: '出货模块', implemented: true },
  { key: 'customer_payment', path: '/payments/customer', title: '客户付款', source: 'Web 收款管理', owner: '收款模块', implemented: true },
  { key: 'supplier_payment', path: '/payments/supplier', title: '供应商付款', source: '原 PyQt 供应商付款', owner: '付款模块', implemented: false },
  { key: 'inventory', path: '/inventory', title: '库存管理', source: '原 PyQt 库存管理', owner: '库存模块', implemented: false },
  { key: 'order_summary', path: '/orders', title: '订单总表', source: 'Web 订单总表', owner: '订单模块', implemented: true },
]
