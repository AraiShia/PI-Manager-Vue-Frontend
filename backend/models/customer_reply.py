"""
客户回复模型
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CustomerReply(Base):
    """客户回复表"""
    __tablename__ = "customer_replies"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pi_id = Column(Integer, ForeignKey("pi_proforma_invoice.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("crm_customer.id", ondelete="CASCADE"), nullable=False, index=True)
    reply_date = Column(Date, nullable=False)
    reply_content = Column(Text, nullable=False)
    # 沟通记录的类型、提交人和同类记录序号由客户往来功能使用。
    # 这些字段必须声明在 ORM 模型中，否则查询/创建时会触发 AttributeError。
    reply_type = Column(String(50), nullable=False, default="reply", server_default="reply")
    submitter_name = Column(String(100), nullable=True)
    sequence_num = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CustomerReply(id={self.id}, pi_id={self.pi_id}, date={self.reply_date})>"
