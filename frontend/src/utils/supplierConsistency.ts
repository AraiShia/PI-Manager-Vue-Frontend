import type { OrderDetailItem } from '@/types/orderSummary'

/**
 * 获取产品项有效供应商名称
 * 优先读取产品自身 supplier_name / factory_name，若为空则取 PI 级别供应商名称
 *
 * @param item 订单明细产品对象
 * @param orderSupplierName PI/订单级别的备用供应商名称
 * @return 去除首尾空格后的供应商名称
 */
export function getItemSupplierName(
  item?: OrderDetailItem | Record<string, unknown> | null,
  orderSupplierName = ''
): string {
  if (!item) {
    return orderSupplierName ? String(orderSupplierName).trim() : ''
  }
  const name =
    (item as any).supplier_name ||
    (item as any).factory_name ||
    orderSupplierName ||
    ''
  return String(name).trim()
}

/**
 * 校验待采购产品列表中各产品的供应商是否完全一致
 * 仅当所有选中的产品供应商完全一致时才允许批量触发采购
 *
 * @param items 待校验的订单明细产品列表
 * @param orderSupplierName PI/订单级别的备用供应商名称
 * @return 若供应商完全一致返回 true，否则返回 false
 */
export function isSupplierConsistent(
  items?: Array<OrderDetailItem | Record<string, unknown>> | null,
  orderSupplierName = ''
): boolean {
  if (!items || items.length <= 1) {
    return true
  }
  const firstSupplier = getItemSupplierName(items[0], orderSupplierName)
  return items.every(
    (it) => getItemSupplierName(it, orderSupplierName) === firstSupplier
  )
}
