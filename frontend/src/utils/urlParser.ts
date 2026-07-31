/**
 * @fileoverview 智能 URL / 1688 采购链接解析工具模块
 * 提供平台识别、1688 Offer ID 提取、域名解析与自动推荐展示名称
 */

export interface ParsedUrlInfo {
  rawUrl: string
  cleanUrl: string
  platform: '1688' | 'taobao' | 'tmall' | 'jd' | 'pinduoduo' | 'amazon' | 'other'
  platformName: string
  tagType: 'danger' | 'warning' | 'success' | 'info' | 'primary'
  offerId?: string
  suggestedDisplayName: string
}

/**
 * 辅助函数：清洗 URL 中的 Slug / 编码文本为规范产品标题
 */
function cleanSlugToTitle(slug: string): string {
  if (!slug) return ''
  try {
    let decoded = decodeURIComponent(slug)
    // 将连字符、下划线、加号替换为空格
    decoded = decoded.replace(/[-_+]/g, ' ')
    // 去除 HTML 后缀如 .html .htm
    decoded = decoded.replace(/\.html?$/i, '')
    // 压缩连续空格
    decoded = decoded.replace(/\s+/g, ' ').trim()
    return decoded
  } catch {
    return slug.replace(/[-_+]/g, ' ').replace(/\.html?$/i, '').trim()
  }
}

/**
 * 自动补全 URL 协议前缀并进行域名与平台解析
 *
 * @param url 待解析的 URL 字符串
 * @returns ParsedUrlInfo 解析结果对象
 */
export function parseShopUrl(url: string): ParsedUrlInfo {
  if (!url || typeof url !== 'string') {
    return {
      rawUrl: '',
      cleanUrl: '',
      platform: 'other',
      platformName: '未知',
      tagType: 'info',
      suggestedDisplayName: '',
    }
  }

  let cleanUrl = url.trim()
  if (!/^https?:\/\//i.test(cleanUrl)) {
    cleanUrl = `https://${cleanUrl}`
  }

  try {
    const parsed = new URL(cleanUrl)
    const hostname = parsed.hostname.toLowerCase()

    // 从 Query 参数提取潜在商品标题
    const paramTitle = parsed.searchParams.get('title') ||
      parsed.searchParams.get('keywords') ||
      parsed.searchParams.get('q') ||
      parsed.searchParams.get('subject') ||
      ''

    // 1. 1688 平台识别
    if (hostname.includes('1688.com')) {
      let offerId: string | undefined
      const offerMatch = parsed.pathname.match(/\/offer\/(\d+)\.html/i) || cleanUrl.match(/offer.*?(\d{7,})/i)
      if (offerMatch) {
        offerId = offerMatch[1]
        // 自动清洗为无追踪参数的标准 Offer URL
        cleanUrl = `https://detail.1688.com/offer/${offerId}.html`
      }

      let displayName = '1688 采购链接'
      if (paramTitle) {
        displayName = `1688 - ${cleanSlugToTitle(paramTitle)}`
      } else if (offerId) {
        displayName = `1688 - 商品 #${offerId}`
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: '1688',
        platformName: '1688 批发网',
        tagType: 'danger',
        offerId,
        suggestedDisplayName: displayName,
      }
    }

    // 2. 淘宝网识别
    if (hostname.includes('taobao.com')) {
      const itemMatch = parsed.searchParams.get('id')
      const title = paramTitle ? cleanSlugToTitle(paramTitle) : ''
      let displayName = '淘宝采购链接'
      if (title) {
        displayName = `淘宝 - ${title}`
      } else if (itemMatch) {
        displayName = `淘宝 - 商品 #${itemMatch}`
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: 'taobao',
        platformName: '淘宝网',
        tagType: 'warning',
        suggestedDisplayName: displayName,
      }
    }

    // 3. 天猫识别
    if (hostname.includes('tmall.com')) {
      const itemMatch = parsed.searchParams.get('id')
      const title = paramTitle ? cleanSlugToTitle(paramTitle) : ''
      let displayName = '天猫采购链接'
      if (title) {
        displayName = `天猫 - ${title}`
      } else if (itemMatch) {
        displayName = `天猫 - 商品 #${itemMatch}`
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: 'tmall',
        platformName: '天猫商城',
        tagType: 'danger',
        suggestedDisplayName: displayName,
      }
    }

    // 4. 京东识别
    if (hostname.includes('jd.com')) {
      const itemMatch = parsed.pathname.match(/\/(\d+)\.html/i)
      const title = paramTitle ? cleanSlugToTitle(paramTitle) : ''
      let displayName = '京东采购链接'
      if (title) {
        displayName = `京东 - ${title}`
      } else if (itemMatch) {
        displayName = `京东 - 商品 #${itemMatch[1]}`
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: 'jd',
        platformName: '京东商城',
        tagType: 'danger',
        suggestedDisplayName: displayName,
      }
    }

    // 5. 拼多多识别
    if (hostname.includes('pinduoduo.com') || hostname.includes('yangkeduo.com')) {
      const title = paramTitle ? cleanSlugToTitle(paramTitle) : ''
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'pinduoduo',
        platformName: '拼多多',
        tagType: 'warning',
        suggestedDisplayName: title ? `拼多多 - ${title}` : '拼多多采购链接',
      }
    }

    // 6. Amazon 识别 (支持提取 URL 路径 Slug 中的实际产品品名)
    if (hostname.includes('amazon.')) {
      const asinMatch = parsed.pathname.match(/\/dp\/([A-Z0-9]{10})/i) ||
        parsed.pathname.match(/\/gp\/product\/([A-Z0-9]{10})/i)
      const asin = asinMatch ? asinMatch[1] : ''

      // 从 /<slug>/dp/<ASIN> 提取 slug 路径片段
      const slugMatch = parsed.pathname.match(/^\/([^\/]+?)\/(?:dp|gp\/product)\//i)
      let titleFromSlug = ''
      if (slugMatch && slugMatch[1] && slugMatch[1].toLowerCase() !== 'dp' && slugMatch[1].toLowerCase() !== 'gp') {
        titleFromSlug = cleanSlugToTitle(slugMatch[1])
      }

      let displayName = 'Amazon 采购链接'
      if (titleFromSlug && asin) {
        displayName = `Amazon - ${titleFromSlug} (${asin})`
      } else if (titleFromSlug) {
        displayName = `Amazon - ${titleFromSlug}`
      } else if (asin) {
        displayName = `Amazon - ASIN ${asin}`
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: 'amazon',
        platformName: 'Amazon',
        tagType: 'primary',
        offerId: asin || undefined,
        suggestedDisplayName: displayName,
      }
    }

    // 7. 其他通用自定义域名 / 独立站 (尝试提取 URL Path 中的商品名称)
    const hostParts = hostname.replace(/^www\./, '').split('.')
    const domainName = hostParts.length >= 2 ? hostParts[0].toUpperCase() : hostname
    
    // 提取 URL Path 最后一部分作为潜在 Slug 名称
    const pathSegments = parsed.pathname.split('/').filter(Boolean)
    let pathSlug = ''
    if (pathSegments.length > 0) {
      const lastSeg = pathSegments[pathSegments.length - 1]
      if (lastSeg && !/^\d+$/.test(lastSeg) && lastSeg.length > 2) {
        pathSlug = cleanSlugToTitle(lastSeg)
      }
    }

    const fallbackName = pathSlug || paramTitle ? cleanSlugToTitle(paramTitle) : ''
    const displayName = fallbackName
      ? `${domainName} - ${fallbackName}`
      : `${domainName} 供应商链接`

    return {
      rawUrl: url,
      cleanUrl,
      platform: 'other',
      platformName: domainName,
      tagType: 'info',
      suggestedDisplayName: displayName,
    }
  } catch (err) {
    return {
      rawUrl: url,
      cleanUrl,
      platform: 'other',
      platformName: '自定义',
      tagType: 'info',
      suggestedDisplayName: '采购链接',
    }
  }
}
