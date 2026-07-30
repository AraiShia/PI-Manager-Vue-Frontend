"""
客户回复CRUD操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, cast
from fastapi import HTTPException
from models.customer_reply import CustomerReply
from models.customer import CrmCustomer
from schemas.customer_reply import CustomerReplyCreate, CustomerReplyUpdate
from crud.pi import resolve_pi


def _generate_sequence_num(db: Session, pi_id: int, reply_type: str) -> int:
    """生成同类回复的序号，防范 sequence_num 为 None 的边界情况"""
    last = db.query(CustomerReply).filter(
        CustomerReply.pi_id == pi_id,
        CustomerReply.reply_type == reply_type
    ).order_by(desc(CustomerReply.sequence_num)).first()
    if last and last.sequence_num is not None:
        return last.sequence_num + 1
    return 1


def _build_sequence_label(reply_type: str, sequence_num: Optional[int]) -> str:
    """构建序号标签 C1, C2, R1, R2"""
    prefix = "C" if reply_type in ("customer", "question") else "R"
    num = sequence_num if sequence_num is not None else 1
    return f"{prefix}{num}"


def get_customer_replies(db: Session, skip: int = 0, limit: int = 100) -> List[CustomerReply]:
    """获取所有客户回复"""
    return db.query(CustomerReply).order_by(desc(CustomerReply.reply_date)).offset(skip).limit(limit).all()


def get_customer_replies_by_pi(db: Session, pi_id: int) -> List[CustomerReply]:
    """获取某PI的所有客户回复，按日期升序"""
    replies = db.query(CustomerReply).filter(
        CustomerReply.pi_id == pi_id
    ).order_by(asc(CustomerReply.reply_date)).all()
    for r in replies:
        r.sequence_label = _build_sequence_label(r.reply_type, r.sequence_num)
    return replies


def get_latest_reply_by_pi(db: Session, pi_id: int) -> Optional[CustomerReply]:
    """获取某PI的最新客户回复"""
    return db.query(CustomerReply).filter(
        CustomerReply.pi_id == pi_id
    ).order_by(desc(CustomerReply.reply_date)).first()


def get_customer_replies_by_customer(db: Session, customer_id: int) -> List[CustomerReply]:
    """获取某客户的所有回复"""
    return db.query(CustomerReply).filter(
        CustomerReply.customer_id == customer_id
    ).order_by(desc(CustomerReply.reply_date)).all()


def get_customer_reply(db: Session, reply_id: int) -> Optional[CustomerReply]:
    """获取单个客户回复"""
    reply = db.query(CustomerReply).filter(CustomerReply.id == reply_id).first()
    if reply:
        reply.sequence_label = _build_sequence_label(reply.reply_type, reply.sequence_num)
    return reply


def create_customer_reply(db: Session, reply: CustomerReplyCreate) -> CustomerReply:
    """创建客户回复，自动解析 PI 及关联客户并安全生成序号"""
    # 1. 解析与验证 PI 实体
    pi_obj = resolve_pi(db, reply.pi_id)
    if not pi_obj:
        raise HTTPException(status_code=404, detail="指定的 PI 单据不存在")

    actual_pi_id = cast(int, pi_obj.id)

    # 2. 自动填充或校验 customer_id
    customer_id = reply.customer_id
    if not customer_id or customer_id <= 0:
        if pi_obj.customer_id:
            customer_id = cast(int, pi_obj.customer_id)
        else:
            raise HTTPException(status_code=400, detail="该 PI 未关联有效客户，无法创建回复记录")

    # 3. 校验客户记录是否存在
    customer = db.query(CrmCustomer).filter(CrmCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail=f"关联的客户信息(ID={customer_id})不存在")

    # 4. 生成序号
    reply_type = reply.reply_type or "reply"
    seq_num = _generate_sequence_num(db, actual_pi_id, reply_type)

    # 5. 构建并写入实体
    db_reply = CustomerReply(
        pi_id=actual_pi_id,
        customer_id=customer_id,
        pi_item_id=getattr(reply, 'pi_item_id', None),
        reply_date=reply.reply_date,
        reply_content=reply.reply_content,
        reply_type=reply_type,
        submitter_name=reply.submitter_name,
        sequence_num=seq_num
    )

    try:
        db.add(db_reply)
        db.commit()
        db.refresh(db_reply)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"保存客户回复记录失败: {str(e)}")

    db_reply.sequence_label = _build_sequence_label(db_reply.reply_type, db_reply.sequence_num)
    return db_reply


def update_customer_reply(db: Session, reply_id: int, reply: CustomerReplyUpdate) -> Optional[CustomerReply]:
    """更新客户回复"""
    db_reply = get_customer_reply(db, reply_id)
    if not db_reply:
        return None

    update_data = reply.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reply, key, value)

    db.commit()
    db.refresh(db_reply)
    db_reply.sequence_label = _build_sequence_label(db_reply.reply_type, db_reply.sequence_num)
    return db_reply


def delete_customer_reply(db: Session, reply_id: int) -> bool:
    """删除客户回复"""
    db_reply = get_customer_reply(db, reply_id)
    if not db_reply:
        return False

    db.delete(db_reply)
    db.commit()
    return True


def get_replies_by_items(db: Session, items: List[dict]) -> List[CustomerReply]:
    """
    按 (pi_id, pi_item_id) 列表批量查询回复记录
    items: [{"pi_id": 1, "pi_item_id": 10}, {"pi_id": 1, "pi_item_id": None}]
    pi_item_id 为 None 时匹配该 PI 下所有未关联商品的回复
    """
    from sqlalchemy import or_

    conditions = []
    for item in items:
        pi_id = item.get("pi_id")
        pi_item_id = item.get("pi_item_id")
        if pi_item_id is not None:
            conditions.append(
                (CustomerReply.pi_id == pi_id) & (CustomerReply.pi_item_id == pi_item_id)
            )
        else:
            conditions.append(
                (CustomerReply.pi_id == pi_id) & (CustomerReply.pi_item_id.is_(None))
            )

    if not conditions:
        return []

    query = db.query(CustomerReply).filter(or_(*conditions))
    replies = query.order_by(asc(CustomerReply.reply_date), asc(CustomerReply.sequence_num)).all()

    for r in replies:
        r.sequence_label = _build_sequence_label(r.reply_type, r.sequence_num)

    return replies