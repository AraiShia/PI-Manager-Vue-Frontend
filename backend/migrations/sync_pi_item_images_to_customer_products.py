"""
同步 PI 明细图片到客户产品表 - REST API 端点

在浏览器/客户端登录后访问此端点，批量将 PI 明细的 temp_image
同步到对应客户产品的 image_url 字段。

幂等：可重复执行，每次只同步客户产品 image_url 为空的记录。

POST /api/migrations/sync-product-images
Response: { "synced": N, "skipped": M, "errors": E }
"""

import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import get_db
from models.pi import PiProformaInvoiceItem
from models.customer_product import PrdCustomerProduct

router = APIRouter(prefix="/api/migrations", tags=["数据迁移"])


class SyncResponse(BaseModel):
    synced: int
    skipped: int
    errors: int


@router.post("/sync-product-images", response_model=SyncResponse)
def sync_product_images(db: Session = Depends(get_db)):
    """
    同步 PI 明细图片到客户产品表

    逻辑：
    - 扫描所有 PI 明细（temp_image 非空、product_id 非空、未软删除）
    - 对每条明细，若对应客户产品 image_url 为空，则写入
    - 已非空的跳过
    """
    synced = 0
    skipped = 0
    errors = 0

    try:
        items = (
            db.query(PiProformaInvoiceItem)
            .filter(
                PiProformaInvoiceItem.is_deleted == False,
                PiProformaInvoiceItem.temp_image.isnot(None),
                PiProformaInvoiceItem.product_id.isnot(None),
            )
            .all()
        )

        for item in items:
            try:
                product = (
                    db.query(PrdCustomerProduct)
                    .filter(PrdCustomerProduct.id == item.product_id)
                    .first()
                )
                if not product:
                    skipped += 1
                    continue
                if product.image_url:
                    skipped += 1
                    continue

                product.image_url = item.temp_image
                synced += 1

            except Exception:
                errors += 1

        db.commit()

    except Exception:
        db.rollback()
        errors += 1

    return SyncResponse(synced=synced, skipped=skipped, errors=errors)
