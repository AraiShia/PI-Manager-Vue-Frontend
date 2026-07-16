const INSECURE_API_ORIGIN = 'http://piapi.wakabashia.tj.cn'
const SECURE_API_ORIGIN = 'https://piapi.wakabashia.tj.cn'

function upgradeUrl(value: string) {
  return value.startsWith(INSECURE_API_ORIGIN)
    ? value.replace(INSECURE_API_ORIGIN, SECURE_API_ORIGIN)
    : value
}

const originalOpen = XMLHttpRequest.prototype.open
XMLHttpRequest.prototype.open = function (
  method: string,
  url: string | URL,
  async?: boolean,
  username?: string | null,
  password?: string | null,
) {
  const nextUrl = typeof url === 'string' ? upgradeUrl(url) : url
  return originalOpen.call(this, method, nextUrl, async ?? true, username ?? null, password ?? null)
}

const originalFetch = window.fetch.bind(window)
window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  if (typeof input === 'string') {
    return originalFetch(upgradeUrl(input), init)
  }
  if (input instanceof URL) {
    return originalFetch(new URL(upgradeUrl(input.href)), init)
  }
  if (input instanceof Request) {
    return originalFetch(new Request(upgradeUrl(input.url), input), init)
  }
  return originalFetch(input, init)
}
