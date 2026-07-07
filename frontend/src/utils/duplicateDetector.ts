/**
 * 重复产品检测工具
 *
 * 提供产品列表的重复判定键提取、重复分组、去重索引计算。
 *
 * 判定优先级：
 *   1) product_id（同一数据库产品）→ product_id:{id}
 *   2) customer_code + oe_number（无 product_id 的临时产品）→ code_oe:{customer_code}|{oe_number}
 *   3) detail_desc（产品名称）→ name:{detail_desc}
 */

export interface DuplicateGroup {
  /** 判定键 */
  key: string
  /** 展示文本（产品名称/编号） */
  display: string
  /** 在原数组中出现的索引列表 */
  indices: number[]
  /** 是否仅因与 existingKeys 冲突而标记为重复（订单内首次出现） */
  external: boolean
}

function normalize(value: any): string {
  if (value === null || value === undefined) return ''
  return String(value).trim()
}

/**
 * 为一行产品提取重复判定键和展示文本
 */
export function extractDuplicateKey(item: any): { key: string; display: string } {
  if (!item) return { key: '', display: '' }

  // 1) product_id 优先
  const productId = item.product_id
  if (productId !== null && productId !== undefined && productId !== 0) {
    const display =
      normalize(item.detail_desc) ||
      normalize(item.product_name) ||
      normalize(item.customer_code) ||
      normalize(item.oe_number) ||
      `产品#${productId}`
    return { key: `product_id:${productId}`, display }
  }

  // 2) customer_code + oe_number 兜底
  const code = normalize(item.customer_code)
  const oe = normalize(item.oe_number)
  if (code || oe) {
    return {
      key: `code_oe:${code}|${oe}`,
      display: code || oe,
    }
  }

  // 3) 产品名称兜底
  const name = normalize(item.detail_desc) || normalize(item.product_name)
  if (name) {
    return { key: `name:${name}`, display: name }
  }

  return { key: '', display: '' }
}

/**
 * 查找产品列表中的重复分组
 */
export function findDuplicates(
  items: any[],
  existingKeys: Set<string> = new Set()
): DuplicateGroup[] {
  const groups = new Map<string, DuplicateGroup>()

  items.forEach((item, idx) => {
    const { key, display } = extractDuplicateKey(item)
    if (!key) return
    if (!groups.has(key)) {
      groups.set(key, { key, display, indices: [], external: false })
    }
    groups.get(key)!.indices.push(idx)
  })

  const duplicates: DuplicateGroup[] = []
  groups.forEach((group) => {
    if (group.indices.length >= 2) {
      duplicates.push(group)
    } else if (existingKeys.has(group.key)) {
      group.external = true
      duplicates.push(group)
    }
  })

  duplicates.sort((a, b) =>
    (a.indices[0] || 0) - (b.indices[0] || 0)
  )
  return duplicates
}

/**
 * 计算"跳过重复行"后应保留的行索引
 */
export function filterDuplicateIndices(
  count: number,
  duplicateGroups: DuplicateGroup[]
): number[] {
  const skip = new Set<number>()
  for (const group of duplicateGroups) {
    if (!group.indices.length) continue
    if (group.external) {
      group.indices.forEach((i) => skip.add(i))
    } else {
      // 保留第一次出现，跳过后续
      group.indices.slice(1).forEach((i) => skip.add(i))
    }
  }
  const result: number[] = []
  for (let i = 0; i < count; i++) {
    if (!skip.has(i)) result.push(i)
  }
  return result
}

/**
 * 判断指定索引是否为重复行
 */
export function isDuplicateIndex(idx: number, groups: DuplicateGroup[]): boolean {
  return groups.some((g) => g.indices.includes(idx))
}
