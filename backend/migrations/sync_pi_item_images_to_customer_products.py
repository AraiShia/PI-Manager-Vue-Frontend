"""同步 PI 明细图片到客户产品表

扫描所有 PI 明细（pi_proforma_invoice_item），将 temp_image 非空的记录，
同步到对应的客户产品（prd_customer_product）的 image_url 字段。

仅同步 product_id 非空、且客户产品 image_url 为空的记录。
可重复执行，是幂等的。

使用方式（在后端服务器上）：
    cd backend
    python migrations/sync_pi_item_images_to_customer_products.py

输出示例：
    扫描 1250 条 PI 明细，找到 87 条有图片且需要同步
    同步 85 条，跳过 2 条（客户产品 image_url 已有值）
    完成。耗时 0.32s
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from models.pi import PiProformaInvoiceItem
from models.customer_product import PrdCustomerProduct


def upgrade(dry_run: bool = False) -> dict:
    db = SessionLocal()
    synced = 0
    skipped = 0
    errors = 0

    try:
        # 只查 temp_image 非空、product_id 非空、且未软删除的明细
        items = (
            db.query(PiProformaInvoiceItem)
            .filter(
                PiProformaInvoiceItem.is_deleted == False,
                PiProformaInvoiceItem.temp_image.isnot(None),
                PiProformaInvoiceItem.product_id.isnot(None),
            )
            .all()
        )

        print(f"扫描 {len(items)} 条 PI 明细（temp_image 非空）...")

        for item in items:
            # 查对应客户产品
            product = db.query(PrdCustomerProduct).filter(
                PrdCustomerProduct.id == item.product_id
            ).first()

            if not product:
                skipped += 1
                continue

            # 已非空则跳过
            if product.image_url:
                skipped += 1
                continue

            if dry_run:
                print(f"  [DRY] item_id={item.id} → product_id={product.id}: {item.temp_image[:60]}")
            else:
                product.image_url = item.temp_image
                print(f"  ✓ item_id={item.id} → product_id={product.id}: {item.temp_image[:60]}")

            synced += 1

        if not dry_run:
            db.commit()
            print(f"已同步 {synced} 条，跳过 {skipped} 条，错误 {errors} 条")
        else:
            print(f"[DRY RUN] 将同步 {synced} 条，跳过 {skipped} 条")

    except Exception as e:
        db.rollback()
        print(f"执行出错: {e}")
        errors += 1
    finally:
        db.close()

    return {"synced": synced, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    if dry:
        print("=== DRY RUN 模式，仅打印不写入 ===\n")

    start = time.time()
    result = upgrade(dry_run=dry)
    print(f"完成。耗时 {time.time() - start:.2f}s")
