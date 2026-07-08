export interface PurchaseFeeFields {
  labeling_fee?: number | null
  tax_fee?: number | null
  shipping_fee?: number | null
  freight?: number | null
  purchase_price?: number | null
}

export interface NormalizedPurchaseFees {
  purchase_price: number
  labeling_fee: number
  tax_fee: number
  shipping_fee: number
  freight: number
  total_cost: number
}

const toNumber = (v: number | null | undefined): number =>
  typeof v === 'number' && Number.isFinite(v) ? v : 0

export function normalizePurchaseFees(input: PurchaseFeeFields = {}): NormalizedPurchaseFees {
  const purchase_price = toNumber(input.purchase_price)
  const labeling_fee = toNumber(input.labeling_fee)
  const tax_fee = toNumber(input.tax_fee)
  const shipping_fee = toNumber(input.shipping_fee)
  const freight = toNumber(input.freight)
  const total_cost = purchase_price + labeling_fee + tax_fee + shipping_fee + freight
  return { purchase_price, labeling_fee, tax_fee, shipping_fee, freight, total_cost }
}

export interface PurchaseSyncTarget {
  purchase_price?: number | null
  labeling_fee?: number | null
  tax_fee?: number | null
  shipping_fee?: number | null
  freight?: number | null
  misc_fee?: number | null
  total_order_amount?: number | null
  supplier_name?: string | null
  shop_url?: string | null
}

export interface PurchaseSyncFields {
  purchase_price: number
  shipping_fee: number
  misc_fee: number
  total_order_amount: number
  supplier_name: string
  shop_url: string
}

export function pickPurchaseSyncFields(
  source: PurchaseFeeFields & { supplier_name?: string | null; shop_url?: string | null },
  fallbackSupplierName = '',
  fallbackShopUrl = ''
): PurchaseSyncFields {
  const fees = normalizePurchaseFees(source)
  return {
    purchase_price: fees.purchase_price,
    shipping_fee: fees.shipping_fee + fees.freight,
    misc_fee: fees.labeling_fee + fees.tax_fee,
    total_order_amount: fees.total_cost,
    supplier_name: (source.supplier_name ?? fallbackSupplierName).toString(),
    shop_url: (source.shop_url ?? fallbackShopUrl).toString(),
  }
}
