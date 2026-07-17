import { describe, it, expect } from 'vitest'
import { splitForHighlight, splitOeInput } from '../customerProduct'

describe('splitForHighlight', () => {
  it('空文本返回空数组', () => {
    expect(splitForHighlight(null, 'abc')).toEqual([])
    expect(splitForHighlight('', 'abc')).toEqual([])
    expect(splitForHighlight(undefined, 'abc')).toEqual([])
  })

  it('无关键词返回单段不命中', () => {
    const r = splitForHighlight('Brake Pad', '')
    expect(r).toEqual([{ text: 'Brake Pad', hit: false }])
  })

  it('大小写不敏感', () => {
    const r = splitForHighlight('Brake Pad', 'brake')
    expect(r).toEqual([{ text: 'Brake', hit: true }, { text: ' Pad', hit: false }])
  })

  it('多段命中', () => {
    const r = splitForHighlight('AXMC 750 brake', 'ax')
    expect(r.some(s => s.hit && s.text.toLowerCase() === 'ax')).toBe(true)
  })

  it('纯数字关键词正常分割', () => {
    const r = splitForHighlight('OE: 601750', '601')
    expect(r).toEqual([{ text: 'OE: ', hit: false }, { text: '601', hit: true }, { text: '750', hit: false }])
  })

  it('关键词含特殊字符转义', () => {
    const r = splitForHighlight('A+B*C', 'A+B')
    expect(r).toEqual([{ text: 'A+B', hit: true }, { text: '*C', hit: false }])
  })
})

describe('splitOeInput', () => {
  it('逗号分隔去重', () => {
    expect(splitOeInput('601, 750, 601')).toEqual(['601', '750'])
  })

  it('斜杠分隔', () => {
    expect(splitOeInput('601/750')).toEqual(['601', '750'])
  })

  it('空格分隔', () => {
    expect(splitOeInput('601   750')).toEqual(['601', '750'])
  })

  it('全角分隔', () => {
    expect(splitOeInput('601、750')).toEqual(['601', '750'])
  })

  it('空输入返回空数组', () => {
    expect(splitOeInput('')).toEqual([])
    expect(splitOeInput('   ,  ')).toEqual([])
  })
})
