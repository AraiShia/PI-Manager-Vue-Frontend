# -*- coding: utf-8 -*-
"""
智能 URL 网页标题抓取与安全解析模块

包含 SSRF 安全审计校验（禁止内网与回环地址）及 HTML <title> / og:title 抓取解析。
"""
import urllib.request
import urllib.parse
import ipaddress
import socket
import re
import html


# 内网与回环地址禁用网段列表
PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]


def is_safe_url(url_str: str) -> tuple[bool, str]:
    """
    SSRF 安全检查：确保 URL 仅使用 http/https 协议，且不指向本地/私有网段 IP。
    """
    if not url_str or not isinstance(url_str, str):
        return False, "URL 不能为空"

    parsed = urllib.parse.urlparse(url_str.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        return False, "仅允许 http 或 https 协议"

    hostname = parsed.hostname
    if not hostname:
        return False, "无效的主机名"

    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0"):
        return False, "禁止访问本地回环地址"

    try:
        # 解析主机 IP 地址
        ip_list = socket.getaddrinfo(hostname, None)
        for item in ip_list:
            ip_str = item[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for private_net in PRIVATE_NETWORKS:
                if ip_obj in private_net:
                    return False, f"禁止访问私有内网 IP ({ip_str})"
    except Exception:
        # 无法解析主机名时交由请求库处理或拒绝
        pass

    return True, "安全 URL"


def fetch_url_title(url_str: str, timeout: float = 3.0) -> str | None:
    """
    发起安全 HTTP GET 请求提取网页纯文本 Title 或 OpenGraph Title。

    :param url_str: 待抓取的网页地址
    :param timeout: 超时时间（秒）
    :return: 清洗后的网页标题，失败返回 None
    """
    is_safe, msg = is_safe_url(url_str)
    if not is_safe:
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        req = urllib.request.Request(url_str, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # 仅读取前 128KB 内容（防止文件过大）
            raw_data = response.read(131072)
            charset = "utf-8"

            # 尝试从 Content-Type 响应头提取字符集
            content_type = response.headers.get("Content-Type", "")
            charset_match = re.search(r"charset=([\w\-]+)", content_type, re.I)
            if charset_match:
                charset = charset_match.group(1)

            try:
                html_text = raw_data.decode(charset, errors="replace")
            except Exception:
                html_text = raw_data.decode("utf-8", errors="replace")

            # 1. 优先提取 OpenGraph / Twitter Meta Title
            og_match = re.search(
                r'<meta\s+(?:property|name)=["\'](?:og:title|twitter:title)["\']\s+content=["\'](.*?)["\']',
                html_text,
                re.I | re.S,
            )
            if not og_match:
                og_match = re.search(
                    r'<meta\s+content=["\'](.*?)["\']\s+(?:property|name)=["\'](?:og:title|twitter:title)["\']',
                    html_text,
                    re.I | re.S,
                )

            title_text = ""
            if og_match:
                title_text = og_match.group(1)
            else:
                # 2. 备选提取常规 <title> 标签
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
                if title_match:
                    title_text = title_match.group(1)

            if title_text:
                # HTML 实体反转义并清洗换行与空白
                cleaned = html.unescape(title_text)
                cleaned = re.sub(r"\s+", " ", cleaned).strip()
                if cleaned:
                    return cleaned
    except Exception:
        pass

    return None
