"""供应商新建 500 修复与联系人扩展属性回归测试用例"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests._helpers import (
    TestingSessionLocal,
    create_test_db,
    drop_test_db,
    install_test_db_dependency,
)

install_test_db_dependency()
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_db():
    create_test_db()
    yield
    drop_test_db()


def test_create_supplier_success_with_contacts_and_city():
    """测试创建带有联系人、电话及省市的供应商，验证 HTTP 200 及联系人属性正确回传"""
    payload = {
        "supplier_name": "洛克希德·马丁",
        "supply_mode": "合同",
        "supplier_wechat": "114514",
        "province": "北京",
        "city": "北京",
        "contact_person": "114514",
        "phone": "114514",
        "platform": "offline",
    }
    response = client.post("/api/suppliers/", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["supplier_name"] == "洛克希德·马丁"
    assert data["contact_person"] == "114514"
    assert data["phone"] == "114514"
    assert data["province"] == "北京"
    assert data["city"] == "北京"
    assert data["city_code"] == "111"
    assert data["supplier_code"].startswith("SP111")


def test_create_supplier_consecutive_increments_code():
    """测试连续创建相同省市供应商，自动自增 supplier_code 且不发生 UNIQUE 冲突 500 错误"""
    payload1 = {
        "supplier_name": "测试供应商A",
        "province": "北京",
        "city": "北京",
        "platform": "offline",
    }
    res1 = client.post("/api/suppliers/", json=payload1)
    assert res1.status_code == 200
    code1 = res1.json()["supplier_code"]

    payload2 = {
        "supplier_name": "测试供应商B",
        "province": "北京",
        "city": "北京",
        "platform": "offline",
    }
    res2 = client.post("/api/suppliers/", json=payload2)
    assert res2.status_code == 200
    code2 = res2.json()["supplier_code"]

    assert code1 != code2
    assert int(code2.replace("SP111", "")) == int(code1.replace("SP111", "")) + 1
