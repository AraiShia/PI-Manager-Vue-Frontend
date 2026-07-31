"""
客户回复 API (POST /api/customer-replies) 单元测试
测试用例覆盖：
1. 正常创建客户回复
2. 省略 customer_id 时自动从 PI 解析并填充
3. 非法/不存在的 PI 单号处理 (404 响应而非 500 崩溃)
4. 非法/不存在的 Customer ID 处理 (400 响应而非 500 崩溃)
5. 防御 sequence_num 为 None 时的异常情况
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from datetime import date
from fastapi.testclient import TestClient

from tests._helpers import (
    create_test_db, drop_test_db, install_test_db_dependency, TestingSessionLocal
)
from main import app
from models import PiProformaInvoice, CrmCustomer
from models.customer_reply import CustomerReply

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    install_test_db_dependency()
    create_test_db()
    db = TestingSessionLocal()
    
    # 插入测试客户
    test_cust = CrmCustomer(
        id=1,
        dept_id="S",
        customer_code="CUST001",
        customer_name="测试客户A",
        status=1
    )
    db.add(test_cust)

    # 插入测试 PI
    test_pi = PiProformaInvoice(
        id=100,
        pi_no="PISO9J02607280",
        dept_id="S",
        customer_id=1,
        total_amount=1000.0,
        status=1
    )
    db.add(test_pi)
    db.commit()
    db.close()
    
    yield
    drop_test_db()


def test_create_customer_reply_success():
    """测试完整参数成功创建客户回复"""
    payload = {
        "pi_id": 100,
        "customer_id": 1,
        "reply_date": "2026-07-30",
        "reply_content": "客户确认订单尺寸符合要求",
        "reply_type": "customer",
        "submitter_name": "张三"
    }
    response = client.post("/api/customer-replies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["pi_id"] == 100
    assert data["customer_id"] == 1
    assert data["sequence_label"] == "C1"


def test_create_customer_reply_auto_resolve_customer_id():
    """测试省略 customer_id 时，自动从 PI 实体绑定 customer_id"""
    payload = {
        "pi_id": 100,
        "reply_date": "2026-07-30",
        "reply_content": "我方已提交最新报价单",
        "reply_type": "reply",
        "submitter_name": "李四"
    }
    response = client.post("/api/customer-replies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == 1
    assert data["sequence_label"] == "R1"


def test_create_customer_reply_non_existent_pi():
    """测试当 PI 不存在时，返回 404 状态码而非 500 服务器错误"""
    payload = {
        "pi_id": 99999,
        "customer_id": 1,
        "reply_date": "2026-07-30",
        "reply_content": "测试不存在的 PI",
    }
    response = client.post("/api/customer-replies", json=payload)
    assert response.status_code == 404
    assert "PI 单据不存在" in response.json()["detail"]


def test_create_customer_reply_non_existent_customer():
    """测试当关联的 Customer 不存在时，返回 400 状态码而非 500 服务器错误"""
    payload = {
        "pi_id": 100,
        "customer_id": 88888,
        "reply_date": "2026-07-30",
        "reply_content": "测试不存在的客户",
    }
    response = client.post("/api/customer-replies", json=payload)
    assert response.status_code == 400
    assert "关联的客户信息" in response.json()["detail"]


def test_create_customer_reply_with_none_sequence_num():
    """测试数据库中既有记录的 sequence_num 为 None 时，不触发 TypeError 500 错误"""
    db = TestingSessionLocal()
    existing_reply = CustomerReply(
        pi_id=100,
        customer_id=1,
        reply_date=date(2026, 7, 29),
        reply_content="已有异常空序号记录",
        reply_type="customer",
        sequence_num=None
    )
    db.add(existing_reply)
    db.commit()
    db.close()

    payload = {
        "pi_id": 100,
        "customer_id": 1,
        "reply_date": "2026-07-30",
        "reply_content": "测试新增同类型记录",
        "reply_type": "customer",
    }
    response = client.post("/api/customer-replies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sequence_num"] == 1
    assert data["sequence_label"] == "C1"


def test_create_and_update_customer_reply_with_pi_item_id():
    """测试带有单品维度 pi_item_id 的创建与更新流程"""
    payload = {
        "pi_id": 100,
        "customer_id": 1,
        "pi_item_id": 501,
        "reply_date": "2026-07-31",
        "reply_content": "客户询问单品包装规格",
        "reply_type": "question",
        "submitter_name": "王五"
    }
    create_res = client.post("/api/customer-replies", json=payload)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["pi_item_id"] == 501
    reply_id = created_data["id"]

    # 测试更新 pi_item_id
    update_payload = {
        "pi_item_id": 502,
        "reply_content": "客户更正单品为 502 并提出新要求"
    }
    update_res = client.put(f"/api/customer-replies/{reply_id}", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["pi_item_id"] == 502
    assert updated_data["reply_content"] == "客户更正单品为 502 并提出新要求"

