# -*- coding: utf-8 -*-
"""
URL Parser 与 SSRF 防御单元测试
"""
import pytest
from app.url_parser import is_safe_url, fetch_url_title


def test_is_safe_url_valid():
    safe, msg = is_safe_url("https://www.amazon.com/dp/B0F15TM77B")
    assert safe is True


def test_is_safe_url_ssrf_blocked():
    # 验证本地回环与私有网段 IP 被正确阻断
    safe_localhost, _ = is_safe_url("http://127.0.0.1:8000/secret")
    assert safe_localhost is False

    safe_private, _ = is_safe_url("http://192.168.1.1/admin")
    assert safe_private is False

    safe_metadata, _ = is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert safe_metadata is False

    safe_invalid_scheme, _ = is_safe_url("file:///etc/passwd")
    assert safe_invalid_scheme is False
