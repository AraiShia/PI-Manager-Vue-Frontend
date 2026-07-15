/**
 * 产品类别硬编码常量
 * 与旧客户端 client/product_categories.py 保持一致
 * 当 API 返回空时兜底使用
 */

export interface ProductCategory {
  code: string
  name: string
  parent_id?: string | null
}

export const FALLBACK_PARENT_CATEGORIES: ProductCategory[] = [
  { code: 'C', name: '汽配件' },
  { code: 'F', name: '办公家具' },
  { code: 'B', name: '百货类' },
]

export const FALLBACK_CHILD_CATEGORIES: ProductCategory[] = [
  { code: 'C01', name: '发动机', parent_id: 'C' },
  { code: 'C02', name: '曲轴', parent_id: 'C' },
  { code: 'C03', name: '刹车片', parent_id: 'C' },
  { code: 'C09', name: '杂项', parent_id: 'C' },
  { code: 'F01', name: '椅子类', parent_id: 'F' },
  { code: 'F02', name: '桌子类', parent_id: 'F' },
  { code: 'F03', name: '柜子类', parent_id: 'F' },
  { code: 'F88', name: '工程定制', parent_id: 'F' },
  { code: 'B00', name: '百货类', parent_id: 'B' },
]
