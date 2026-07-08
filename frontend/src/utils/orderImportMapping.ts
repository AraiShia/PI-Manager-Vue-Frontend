export interface ImportColumnMapping {
  product_code?: string
  customer_model?: string
  oe_number?: string
  product_name?: string
  product_name_en?: string
  product_acquires?: string
  quantity?: string
  unit_price?: string
  remark?: string
  remarkParts?: string[]
  product_feature?: string
}

export interface ImportFieldDef {
  key: string
  label: string
  required?: boolean
}

export const DEFAULT_IMPORT_FIELDS: ImportFieldDef[] = [
  { key: 'customer_model', label: '客户型号', required: true },
  { key: 'product_code', label: '编号备注', required: false },
  { key: 'oe_number', label: 'OE号', required: false },
  { key: 'product_name', label: '产品名称', required: false },
  { key: 'product_name_en', label: '英文名称', required: false },
  { key: 'product_acquires', label: '产品需求', required: false },
  { key: 'quantity', label: '数量', required: true },
  { key: 'unit_price', label: '报价', required: false },
  { key: 'remark', label: '客户需求/产品备注', required: false },
  { key: 'product_feature', label: '产品特性', required: false },
]

const keywordMap: Record<keyof ImportColumnMapping, string[]> = {
  customer_model: ['客户型号(model)', '客户型号', 'model', 'customer_model'],
  product_code: ['编号备注', '客户产品编号', '产品编号', '产品编码', 'product_code', 'product code'],
  oe_number: ['oe号', 'oe编号', 'oe_number', 'oe number'],
  product_name: ['产品名称', '品名', 'product_name', 'product name', 'p-name'],
  product_name_en: ['英文名称', '英文名', 'product_name_en', 'english name', 'p-name en'],
  product_acquires: ['产品需求', 'p-details', 'product_acquires', 'product requires', 'requirement'],
  quantity: ['数量', '订货数量', 'quantity', 'qty'],
  unit_price: ['报价', '单价', '价格', 'unit_price', 'unit price', 'price'],
  remark: ['客户需求/产品备注', '客户需求', '产品备注', '备注', 'remark', 'note'],
  remarkParts: [],
  product_feature: ['产品特性', '特性', 'product_feature', 'feature'],
}

function normalizeHeader(header: string): string {
  return String(header || '').trim().toLowerCase()
}

function matchHeader(headers: string[], keywords: string[]): string {
  for (const keyword of keywords) {
    const normalizedKeyword = normalizeHeader(keyword)
    const exact = headers.find((h) => normalizeHeader(h) === normalizedKeyword)
    if (exact) return exact
  }
  for (const keyword of keywords) {
    const normalizedKeyword = normalizeHeader(keyword)
    const partial = headers.find((h) => normalizeHeader(h).includes(normalizedKeyword))
    if (partial) return partial
  }
  return ''
}

export function autoMapImportColumns(headers: string[]): Record<string, string> {
  const mapping: Record<string, string> = {}
  for (const field of DEFAULT_IMPORT_FIELDS) {
    mapping[field.key] = matchHeader(headers, keywordMap[field.key as keyof ImportColumnMapping] || [])
  }
  return mapping
}

function pick(row: Record<string, any>, columnName?: string): any {
  return columnName ? row[columnName] : undefined
}

function joinNonEmpty(values: any[], delimiter = ', '): string {
  return values
    .map((value) => String(value ?? '').trim())
    .filter(Boolean)
    .join(delimiter)
}

export function buildImportItemFromRow(
  row: Record<string, any>,
  mapping: ImportColumnMapping,
  importSeq: number
): Record<string, any> {
  const item: Record<string, any> = { import_seq: importSeq }
  const directFields: (keyof ImportColumnMapping)[] = [
    'customer_model',
    'product_code',
    'oe_number',
    'product_name',
    'product_name_en',
    'product_acquires',
    'quantity',
    'unit_price',
    'remark',
    'product_feature',
  ]

  for (const field of directFields) {
    const columnName = mapping[field]
    if (typeof columnName === 'string' && columnName) {
      item[field] = pick(row, columnName)
    }
  }

  if (mapping.remarkParts?.length) {
    item.remark = joinNonEmpty(mapping.remarkParts.map((column) => pick(row, column)))
  }

  return item
}

export function buildDisplayProductName(productName?: string | null, productNameEn?: string | null): string[] {
  return [productName, productNameEn]
    .map((value) => String(value ?? '').trim())
    .filter(Boolean)
}

export function buildDisplayRemark(acquires?: string | null, color?: string | null): string[] {
  return [acquires, color]
    .map((value) => String(value ?? '').trim())
    .filter(Boolean)
}
