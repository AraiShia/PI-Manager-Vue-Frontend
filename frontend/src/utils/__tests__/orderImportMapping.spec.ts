import { describe, expect, it } from 'vitest'
import {
  autoMapImportColumns,
  buildDisplayProductName,
  buildDisplayRemark,
  buildImportItemFromRow,
} from '../orderImportMapping'

describe('order import mapping', () => {
  it('maps Model to customer_model and Qty to quantity', () => {
    const mapping = autoMapImportColumns(['Model', 'Qty'])
    expect(mapping.customer_model).toBe('Model')
    expect(mapping.quantity).toBe('Qty')
    expect(mapping.product_code).toBe('')
  })

  it('maps product requirement headers to product_acquires', () => {
    const mapping = autoMapImportColumns(['产品需求', 'Qty'])
    expect(mapping.product_acquires).toBe('产品需求')
  })

  it('builds import item with comma-joined code remark and direct product_acquires', () => {
    const item = buildImportItemFromRow(
      {
        Model: 'AAAAAAA',
        Qty: 300,
        编号备注: 'QTY: 300',
        ExtraNote: 'MODEL: AAAAAAA',
        产品需求: '需要黑色外壳',
      },
      {
        customer_model: 'Model',
        quantity: 'Qty',
        product_code: '',
        product_name: '',
        product_name_en: '',
        remarkParts: ['编号备注', 'ExtraNote'],
        product_acquires: '产品需求',
      },
      1
    )

    expect(item.customer_model).toBe('AAAAAAA')
    expect(item.quantity).toBe(300)
    expect(item.remark).toBe('QTY: 300, MODEL: AAAAAAA')
    expect(item.product_acquires).toBe('需要黑色外壳')
    expect(item.import_seq).toBe(1)
  })

  it('builds display product name with Chinese and English on separate lines', () => {
    expect(buildDisplayProductName('中文名', 'English Name')).toEqual(['中文名', 'English Name'])
    expect(buildDisplayProductName('中文名', '')).toEqual(['中文名'])
    expect(buildDisplayProductName('', 'English Name')).toEqual(['English Name'])
  })

  it('buildDisplayRemark renders product_acquires and product_color on separate lines', () => {
    expect(buildDisplayRemark('需要3C认证', '红色')).toEqual(['需要3C认证', '红色'])
    expect(buildDisplayRemark('需要3C认证', '')).toEqual(['需要3C认证'])
    expect(buildDisplayRemark('', '红色')).toEqual(['红色'])
    expect(buildDisplayRemark('', '')).toEqual([])
    expect(buildDisplayRemark(null, null)).toEqual([])
  })
})
