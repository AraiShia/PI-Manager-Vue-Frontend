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

    // 1. 1688 平台识别
    if (hostname.includes('1688.com')) {
      let offerId: string | undefined
      const offerMatch = parsed.pathname.match(/\/offer\/(\d+)\.html/i) || cleanUrl.match(/offer.*?(\d{7,})/i)
      if (offerMatch) {
        offerId = offerMatch[1]
      }

      return {
        rawUrl: url,
        cleanUrl,
        platform: '1688',
        platformName: '1688 批发网',
        tagType: 'danger',
        offerId,
        suggestedDisplayName: offerId ? `1688 - 商品 #${offerId}` : '1688 采购链接',
      }
    }

    // 2. 淘宝网识别
    if (hostname.includes('taobao.com')) {
      const itemMatch = parsed.searchParams.get('id')
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'taobao',
        platformName: '淘宝网',
        tagType: 'warning',
        suggestedDisplayName: itemMatch ? `淘宝 - 商品 #${itemMatch}` : '淘宝采购链接',
      }
    }

    // 3. 天猫识别
    if (hostname.includes('tmall.com')) {
      const itemMatch = parsed.searchParams.get('id')
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'tmall',
        platformName: '天猫商城',
        tagType: 'danger',
        suggestedDisplayName: itemMatch ? `天猫 - 商品 #${itemMatch}` : '天猫采购链接',
      }
    }

    // 4. 京东识别
    if (hostname.includes('jd.com')) {
      const itemMatch = parsed.pathname.match(/\/(\d+)\.html/i)
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'jd',
        platformName: '京东商城',
        tagType: 'danger',
        suggestedDisplayName: itemMatch ? `京东 - 商品 #${itemMatch[1]}` : '京东采购链接',
      }
    }

    // 5. 拼多多识别
    if (hostname.includes('pinduoduo.com') || hostname.includes('yangkeduo.com')) {
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'pinduoduo',
        platformName: '拼多多',
        tagType: 'warning',
        suggestedDisplayName: '拼多多采购链接',
      }
    }

    // 6. Amazon 识别
    if (hostname.includes('amazon.com') || hostname.includes('amazon.cn')) {
      const asinMatch = parsed.pathname.match(/\/dp\/([A-Z0-9]{10})/i)
      return {
        rawUrl: url,
        cleanUrl,
        platform: 'amazon',
        platformName: 'Amazon',
        tagType: 'primary',
        suggestedDisplayName: asinMatch ? `Amazon - ASIN ${asinMatch[1]}` : 'Amazon 采购链接',
      }
    }

    // 7. 其他通用自定义域名
    const hostParts = hostname.replace(/^www\./, '').split('.')
    const domainName = hostParts.length >= 2 ? hostParts[0].toUpperCase() : hostname
    return {
      rawUrl: url,
      cleanUrl,
      platform: 'other',
      platformName: domainName,
      tagType: 'info',
      suggestedDisplayName: `${domainName} 供应商链接`,
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
